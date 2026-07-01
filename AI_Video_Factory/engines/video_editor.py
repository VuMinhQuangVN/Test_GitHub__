# engines/video_editor.py
import os
import PIL.Image

# --- FIX LỖI PIL.Image.ANTIALIAS ---
# Đoạn này giúp MoviePy tương thích với các bản Pillow mới nhất
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS
# -----------------------------------

from moviepy.editor import VideoFileClip, concatenate_videoclips, vfx, CompositeVideoClip, ImageClip
from moviepy.config import change_settings

class VideoEditorEngine:
    def __init__(self):
        """Khởi tạo cỗ máy biên tập"""
        pass

    def time_to_seconds(self, time_str):
        """Helper: Chuyển '0:01.20' hoặc '1.2s' sang float"""
        time_str = str(time_str).replace('s', '').strip()
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 2: # mm:ss.ms
                return int(parts[0]) * 60 + float(parts[1])
            elif len(parts) == 3: # hh:mm:ss.ms
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        return float(time_str)

    def assemble_fashion_story(self, edl_json, base_folder, output_path, sticker_path=None):
        """Lõi A: Ghép nhiều shot từ EDL (Fashion Story)"""
        segments = []
        edl_data = edl_json.get("edl", [])
        
        try:
            for item in edl_data:
                video_name = item["source"]
                video_full_path = os.path.join(base_folder, video_name)
                
                if not os.path.exists(video_full_path):
                    print(f"⚠️ Missing: {video_name}")
                    continue
                    
                clip = VideoFileClip(video_full_path)
                duration = clip.duration # Lấy độ dài thực tế của clip (thường là 8.0)
                
                # Parse source range
                start_str, end_str = item["sourceRange"].split(" - ")
                start_t = self.time_to_seconds(start_str)
                end_t = self.time_to_seconds(end_str)

                # --- CHỐNG TRÀN THỜI GIAN (Duration Safety) ---
                # Đảm bảo thời gian cắt không vượt quá độ dài thực tế của clip
                if start_t >= duration:
                    start_t = max(0, duration - 1.0)
                
                if end_t > duration:
                    end_t = duration
                
                if start_t >= end_t:
                    start_t = max(0, end_t - 0.5)
                # -----------------------------------------------
                
                # Cắt clip
                sub_clip = clip.subclip(start_t, end_t)
                
                # Xử lý hiệu ứng Speed
                if "Slow motion" in item.get("effects", ""):
                    sub_clip = sub_clip.fx(vfx.speedx, 0.5)
                elif "Speed ramp" in item.get("effects", ""):
                    sub_clip = sub_clip.fx(vfx.speedx, 1.5)
                
                segments.append(sub_clip)

            if not segments: return None

            # Ghép mạch phim
            final_video = concatenate_videoclips(segments, method="compose")

            # Chèn nhãn dán che logo (Watermark Masking)
            if sticker_path and os.path.exists(sticker_path):
                sticker = (ImageClip(sticker_path)
                           .set_duration(final_video.duration)
                           .resize(height=100) 
                           .set_position(("right", "bottom")))
                final_video = CompositeVideoClip([final_video, sticker])

            # Xuất video (fps=30 là chuẩn cho TikTok)
            final_video.write_videofile(output_path, fps=30, codec="libx264", audio=False)
            return output_path
            
        except Exception as e:
            print(f"❌ Error during assembly: {e}")
            return None

    def process_batch_showcase(self, video_path, output_path, sticker_path=None):
        """Lõi B: 1 clip 8s -> 12s (Phụ kiện)"""
        try:
            clip = VideoFileClip(video_path)
            # Giảm tốc độ xuống 0.67x để từ 8s thành ~12s
            final_clip = clip.fx(vfx.speedx, 0.67)
            
            if sticker_path and os.path.exists(sticker_path):
                sticker = (ImageClip(sticker_path)
                           .set_duration(final_clip.duration)
                           .resize(height=80)
                           .set_position(("right", "bottom")))
                final_clip = CompositeVideoClip([final_clip, sticker])
                
            final_clip.write_videofile(output_path, fps=30, codec="libx264", audio=False)
            return output_path
        except Exception as e:
            print(f"❌ Error during batch process: {e}")
            return None