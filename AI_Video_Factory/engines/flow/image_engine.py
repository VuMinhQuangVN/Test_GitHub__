import os
import shutil
from playwright.sync_api import sync_playwright
from core.browser_manager import BrowserManager
from core.prompt_builder import PromptBuilder
from pages.flow_image import FlowImagePage

class ImageEngine:
    def __init__(self, app_instance):
        self.app = app_instance
        self.builder = PromptBuilder()
        self.pro_profile = "chrome_auto_profile"

    def run_full_pipeline(self, sku, product_type_vn, style, scene, char_path, prod_path):
        """
        Quy trình sạch: 
        1. Tạo các prompt từ template.
        2. Dùng Flow (Banana Pro) tạo ra list ảnh phôi.
        3. Lưu thông tin để chuẩn bị đẩy qua ChatGPT.
        """
        sku_folder = os.path.join(self.app.mgr.base_path, sku)
        os.makedirs(sku_folder, exist_ok=True)
        
        # Tạo danh sách các prompt cần vẽ
        tasks = self.builder.build_image_prompts(product_type_vn, style, scene)
        generated_images = []

        try:
            with sync_playwright() as p:
                mgr = BrowserManager(profile_name=self.pro_profile)
                context = mgr.init_browser(p)
                page = context.pages[0]
                bot = FlowImagePage(page)
                bot.navigate()

                for task in tasks:
                    self.app.write_log(f"🎨 Đang vẽ ảnh: {task['type']} cho SKU {sku}")
                    
                    # Điền nốt thông tin ảnh sản phẩm vào prompt (nếu cần mô tả)
                    final_prompt = task['prompt'].replace("{product_image}", "the provided product image")
                    
                    # Gọi Page để vẽ (Truyền cả ảnh người mẫu và ảnh sản phẩm làm tham chiếu)
                    img_path = bot.create_base_images(
                        image_paths=[char_path, prod_path],
                        prompt_text=final_prompt,
                        save_dir=sku_folder,
                        sku=f"{sku}_{task['type']}"
                    )
                    
                    if img_path:
                        generated_images.append({
                            "type": task['type'],
                            "path": img_path,
                            "base_prompt": final_prompt
                        })

                context.close()
                mgr.cleanup_profile()

            # Sau khi tạo xong ảnh, lưu vào info.json để Video Engine biết đường mà lần
            self.app.mgr.save_sku_metadata(sku, char_path, product_type_vn, prod_path)
            
            return generated_images

        except Exception as e:
            self.app.write_log(f"❌ Lỗi ImageEngine: {e}")
            return []

    def cleanup_temp_files(self, sku):
        """Hàm dọn dẹp sau khi Video đã tạo thành công (để dành gọi sau)"""
        sku_folder = os.path.join(self.app.mgr.base_path, sku, "base_image")
        if os.path.exists(sku_folder):
            shutil.rmtree(sku_folder)
            self.app.write_log(f"🧹 Đã dọn dẹp ảnh tạm cho {sku}")