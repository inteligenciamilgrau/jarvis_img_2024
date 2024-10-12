import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import random
import time

class ImageSelectionGame:
    def __init__(self, master):
        self.master = master
        self.master.title("Image Selection Game")

        # Get the screen width and height
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # Get the actual position of the second monitor
        second_monitor_x = self.master.winfo_x()
        second_monitor_y = self.master.winfo_y()

        print("SCREEN", screen_width, screen_height)
        print("SECOND MONITOR POSITION", second_monitor_x, second_monitor_y)

        # Calculate the starting position to center the window on the second monitor
        monitor_width = 800  # Set the desired width of the window
        monitor_height = 600  # Set the desired height of the window
        segundo_monitor_pixels = 1910
        x = segundo_monitor_pixels
        y = 0 #second_monitor_y + (screen_height - monitor_height) // 2

        self.master.geometry(f"{monitor_width}x{monitor_height}+{x}+{y}")  # Set the window size and position

        self.image_folder = os.path.join(os.path.dirname(__file__), "images")  # Use relative path
        self.image_files = self.get_image_files()

        if len(self.image_files) < 4:
            messagebox.showerror("Error", "Not enough images in the folder. Please add at least 4 images.")
            self.master.quit()
            return

        self.selected_images = random.sample(self.image_files, 4)
        self.target_image = random.choice(self.selected_images)

        self.image_size = 100
        self.image_objects = []

        self.create_widgets()

    def get_image_files(self):
        return [f for f in os.listdir(self.image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]

    def create_widgets(self):
        self.message_label = tk.Label(self.master, font=("Arial", 16))
        self.message_label.pack(pady=10, padx=10)
        self.update_message_label()

        self.canvas = tk.Canvas(self.master, width=780, height=500, bg='white')
        self.canvas.pack(padx=0, pady=0)

        self.result_label = tk.Label(self.master, font=("Arial", 16))
        self.result_label.place(relx=0.5, rely=0.8, anchor="center")

        self.place_images()

    def start_new_game(self):
        self.canvas.delete("all")
        self.selected_images = random.sample(self.image_files, 4)
        self.target_image = random.choice(self.selected_images)
        self.place_images()
        self.result_label.config(text="")  # Clear the result label
        self.message_label.config(text=f"Click on the {os.path.splitext(self.target_image)[0]}")

    def place_images(self):
        self.canvas.delete("all")
        placed_rects = []
        for image_file in self.selected_images:
            img = Image.open(os.path.join(self.image_folder, image_file))
            img = img.resize((self.image_size, self.image_size), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            while True:
                x = random.randint(0, 780 - self.image_size)
                y = random.randint(0, 500 - self.image_size)
                new_rect = (x, y, x + self.image_size, y + self.image_size)
                
                if not any(self.rectangles_overlap(new_rect, rect) for rect in placed_rects):
                    placed_rects.append(new_rect)
                    break

            image_item = self.canvas.create_image(x, y, anchor=tk.NW, image=photo)
            self.canvas.tag_bind(image_item, '<Button-1>', lambda event, img=image_file: self.check_selection(img))
            self.image_objects.append(photo)  # Keep a reference to prevent garbage collection

    def update_message_label(self):
        self.message_label.config(text=f"Click on the {os.path.splitext(self.target_image)[0]}")

    def rectangles_overlap(self, rect1, rect2):
        return not (rect1[2] <= rect2[0] or rect1[0] >= rect2[2] or rect1[3] <= rect2[1] or rect1[1] >= rect2[3])

    def check_selection(self, selected_image):
        if selected_image == self.target_image:
            self.result_label.config(text="Correct! You won!", fg="green")
            self.master.after(2000, self.start_new_game)
        else:
            self.result_label.config(text="Sorry, that's incorrect. Try again!", fg="red")
            self.master.after(1000, self.reset_result_label)

    def reset_result_label(self):
        self.result_label.config(text="")


def main():
    root = tk.Tk()
    game = ImageSelectionGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()
