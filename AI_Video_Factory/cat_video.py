import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import threading
from moviepy.editor import VideoFileClip

class VideoSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Phần mềm cắt Video 5s - Python")
        self.root.geometry("600x500")

        # Biến lưu đường dẫn
        self.video_path = tk.StringVar()
        self.save_dir = tk.StringVar()

        # --- Giao diện ---
        # Chọn Video
        tk.Label(root, text="1. Chọn Video đầu vào:", font=("Arial", 10, "bold")).pack(pady=(10, 0), anchor="w", padx=20)
        entry_frame1 = tk.Frame(root)
        entry_frame1.pack(fill="x", padx=20)
        tk.Entry(entry_frame1, textvariable=self.video_path, width=50).pack(side="left", pady=5)
        tk.Button(entry_frame1, text="Duyệt file", command=self.browse_video).pack(side="left", padx=5)

        # Chọn nơi lưu
        tk.Label(root, text="2. Chọn thư mục lưu các đoạn cắt:", font=("Arial", 10, "bold")).pack(pady=(10, 0), anchor="w", padx=20)
        entry_frame2 = tk.Frame(root)
        entry_frame2.pack(fill="x", padx=20)
        tk.Entry(entry_frame2, textvariable=self.save_dir, width=50).pack(side="left", pady=5)
        tk.Button(entry_frame2, text="Duyệt thư mục", command=self.browse_folder).pack(side="left", padx=5)

        # Nút bắt đầu
        self.btn_start = tk.Button(root, text="BẮT ĐẦU CẮT VIDEO", bg="#27ae60", fg="white", 
                                   font=("Arial", 12, "bold"), height=2, width=20, command=self.start_processing_thread)
        self.btn_start.pack(pady=20)

        # Log hiển thị quá trình
        tk.Label(root, text="Tiến trình:").pack(anchor="w", padx=20)
        self.log_area = scrolledtext.ScrolledText(root, width=70, height=12)
        self.log_area.pack(pady=5, padx=20)

    def browse_video(self):
        file_selected = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.mov *.avi *.mkv")])
        if file_selected:
            self.video_path.set(file_selected)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.save_dir.set(folder_selected)

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def start_processing_thread(self):
        if not self.video_path.get() or not self.save_dir.get():
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn đầy đủ video và nơi lưu!")
            return

        threading.Thread(target=self.process_video, daemon=True).start()

    def process_video(self):
        input_file = self.video_path.get()
        output_folder = self.save_dir.get()
        segment_duration = 7

        try:
            self.btn_start.config(state=tk.DISABLED)
            self.log_area.delete('1.0', tk.END) # Xóa log cũ
            self.log("Đang tải video... Vui lòng đợi.")
            
            video = VideoFileClip(input_file)
            total_duration = video.duration
            self.log(f"Tổng thời lượng: {total_duration:.2f} giây.")

            start_time = 0
            part_number = 1

            while start_time < total_duration:
                end_time = start_time + segment_duration
                if end_time > total_duration:
                    end_time = total_duration

                output_filename = os.path.join(output_folder, f"segment_{part_number:03d}.mp4")
                self.log(f"Đang cắt đoạn {part_number}: {start_time}s -> {end_time}s")
                
                subclip = video.subclip(start_time, end_time)
                # Dùng logger=None để MoviePy không in log rác ra console
                subclip.write_videofile(output_filename, codec="libx264", audio_codec="aac", verbose=False, logger=None)

                start_time += segment_duration
                part_number += 1

            video.close()
            self.log("--- HOÀN THÀNH ---")
            messagebox.showinfo("Thành công", f"Đã cắt xong thành {part_number-1} đoạn!")
            
        except Exception as e:
            self.log(f"LỖI: {str(e)}")
            messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
        
        finally:
            self.btn_start.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoSplitterApp(root)
    root.mainloop()