import os
import argparse
import sys
import time
import piexif
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

def find_empty_spot(width, height, padding, img_width, img_height):
    num_cols = (width + padding) // (img_width +  padding)
    num_rows = (height +  padding) // (img_height +  padding)

    for row_idx in range(num_rows):
        for col_idx in range(num_cols):
            x_offset = col_idx * (img_width +  padding) +  padding
            y_offset = row_idx * (img_height +  padding) +  padding

            if (x_offset + img_width +  padding <= width) and (y_offset + img_height + padding <= height):
                return x_offset, y_offset

    return None

def load_images(directory):
    images = []
    for filename in os.listdir(directory):
        try:
            file_path = os.path.join(directory, filename)
            img = Image.open(file_path)
            created_date = extract_creation_date(file_path)
            images.append((img.copy(), filename, created_date))
            img.close()
        except IOError:
            print(f"Could not open or process '{filename}'. Skipping this file.")
    return images

def extract_creation_date(image_path):
    try:
        exif_dict = piexif.load(image_path)
        if piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']:
            date_str = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
            return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except Exception as e:
        print(f"Error extracting creation date from '{image_path}': {e}")
    return datetime.fromtimestamp(os.path.getmtime(image_path))  # fallback to modification time

def create_collage(imgs, collage_id, width, height, p, verbose=True):
    num_imgs = len(imgs)
    num_cols = int(num_imgs ** 0.5)
    num_rows = -(-num_imgs // num_cols)

    img_width, img_height = (width - p['padding'] * (num_cols + 1)) // num_cols, (height - p['padding'] * (num_rows + 1)) // num_rows

    collage = Image.new('RGBA', (width, height), color=p['bg_color'])

    font = ImageFont.truetype(p['font'], size=p['text_size'])

    for i, (img, filename, created_date) in enumerate(imgs):

        row_idx, col_idx = divmod(i, num_cols)

        if img.size[0] > img.size[1] and width < height or img.size[0] < img.size[1] and width > height:
            img = img.rotate(90, expand=True)

        scale = min(img_width / img.size[0], img_height / img.size[1])

        img = img.resize((int(img.size[0] * scale), int(img.size[1] * scale)), resample=Image.LANCZOS)

        if verbose:
            created_date = datetime.fromtimestamp(os.path.getmtime(os.path.join('images', filename))).strftime(p['date_format'])
            print(f"Processing image '{filename}': created {created_date}, original size {img.size}, scaled size {img.size[0] * scale, img.size[1] * scale}")

        if p['align'] == 'left':
            x_offset = col_idx * (img_width + p['padding']) + p['padding']
        elif p['align'] == 'right':
            x_offset = (col_idx + 1) * (img_width + p['padding']) - img.size[0]
        else:  # center
            x_offset = col_idx * (img_width + p['padding']) + (img_width - img.size[0]) // 2 + p['padding']

        y_offset = row_idx * (img_height + p['padding']) + (img_height - img.size[1]) // 2 + p['padding']

        if p['border']:
            img_with_border = Image.new('RGB', (img.size[0] + p['border_thickness'] * 2, img.size[1] + p['border_thickness'] * 2), color=p['border_color'])
            img_with_border.paste(img, (p['border_thickness'], p['border_thickness']))
            img = img_with_border

        if img.mode == 'RGBA':
            alpha = Image.new('L', img.size, 255)
            alpha.paste(img.split()[3], (0, 0), img.split()[3])
            collage.paste(img, (x_offset, y_offset), mask=alpha)
        else:
            collage.paste(img, (x_offset, y_offset))

        draw = ImageDraw.Draw(collage)
        date_str = datetime.fromtimestamp(os.path.getmtime(os.path.join('images', os.listdir('images')[i]))).strftime(p['date_format'])
        text_opacity = int(255 * p['text_opacity'])
        draw.text((x_offset + p['border_thickness'] + 1, y_offset + p['border_thickness'] + 1), date_str, font=font, fill=(0, 0, 0, text_opacity))
        draw.text((x_offset + p['border_thickness'], y_offset + p['border_thickness']), date_str, font=font, fill=(255, 255, 255, text_opacity))

    if p['info_box']:
        info_text = f"Date: {datetime.now().strftime(p['date_format'])}\nParameters:\n{p}"
        info_font = ImageFont.truetype(p['font'], size=16)
        info_draw = ImageDraw.Draw(collage)
        info_bbox = info_draw.multiline_textbbox((0, 0), info_text, font=info_font)

        info_w, info_h = int(info_bbox[2] - info_bbox[0]), int(info_bbox[3] - info_bbox[1])
        info_box = Image.new('RGBA', (info_w + 20, info_h + 20), color=(128, 128, 128, 128))
        info_draw = ImageDraw.Draw(info_box)
        info_draw.multiline_text((10, 10), info_text, font=info_font, fill=(255, 255, 255))
        empty_spot = find_empty_spot(width, height, p['padding'], info_w + 20, info_h + 20)

        if empty_spot:
            collage.paste(info_box, empty_spot, info_box)
        else:
            print("Could not find an empty spot for the info box.")

    collage_filename = f"{p['prefix']}-{datetime.now().strftime('%Y%m%d')}-{collage_id}.png"
    i = 1
    while os.path.exists(collage_filename):
        collage_filename = f"{p['prefix']}-{datetime.now().strftime('%Y%m%d')}-{collage_id}-{i}.png"
        i += 1

    collage.save(collage_filename)
    print(f"Collage {collage_id} saved as {collage_filename}")

    if verbose:
        collage_size = os.path.getsize(collage_filename)
        print(f"Collage {collage_id} file size: {collage_size} bytes")


def main():
    parser = argparse.ArgumentParser(description='Generate image collages with custom settings.')
    parser.add_argument('-v', '--verbose', action='store_true', default=True, help='Enable verbose output.')
    parser.add_argument('-f', '--folder', type=str, default='images', help='Folder containing the images.')
    parser.add_argument('--width', type=int, default=5100, help='Width of collage image.')
    parser.add_argument('--height', type=int, default=6600, help='Height of collage image.')
    parser.add_argument('-F', '--font', type=str, default=None, help='Font filename for the text.')
    parser.add_argument('-p', '--pics-per-page', type=int, default=30, help='Amount of pictures per collage page.')
    parser.add_argument('-b', '--border', action='store_false', help='Enable border around images.')
    parser.add_argument('-t', '--border-thickness', type=int, default=4, help='Border thickness around images.')
    parser.add_argument('-c', '--border-color', type=str, default='255,255,255', help='Border color around images (R,G,B).')
    parser.add_argument('-P', '--padding', type=int, default=6, help='Padding between images in pixels.')
    parser.add_argument('-a', '--align', type=str, choices=['left', 'center', 'right'], default='left', help='Alignment of images in each column.')
    parser.add_argument('-s', '--text-size', type=int, default=32, help='Size of the text.')
    parser.add_argument('-o', '--text-opacity', type=float, default=1.0, help='Opacity of the text (0 to 1).')
    parser.add_argument('-d', '--date-format', type=str, default='%m-%d', help='Date format for image dates. ') # %Y-%m-%d
    parser.add_argument('-x', '--prefix', type=str, default='collage', help='Filename prefix for the collage.')
    parser.add_argument('-g', '--bg-color', type=str, default='255,255,255', help='Background color for the canvas (R,G,B).')
    parser.add_argument('-i', '--info-box', action='store_true', help='Enable info box with date and parameters.')

    args = parser.parse_args()

    # Convert comma-separated RGB strings to tuples
    border_color = tuple(map(int, args.border_color.split(',')))
    bg_color = tuple(map(int, args.bg_color.split(',')))

    def get_default_font():
        if sys.platform.startswith('win'):  # Windows
            return 'arial.ttf'
        elif sys.platform.startswith('darwin'):  # macOS
            return 'Arial.ttf'
        elif sys.platform.startswith('linux'):  # Linux
            return '/usr/share/fonts/truetype/freefont/FreeSans.ttf'
        else:
            raise ValueError("Unsupported operating system.")
    
    params = {
        'width': args.width,
        'height': args.height,
        'pics_per_page': args.pics_per_page,
        'border': args.border,
        'border_thickness': args.border_thickness,
        'border_color': border_color,
        'padding': args.padding,
        'align': args.align,
        'font': args.font if args.font else get_default_font(),
        'text_size': args.text_size,
        'text_opacity': args.text_opacity,
        'date_format': args.date_format,
        'prefix': args.prefix,
        'bg_color': bg_color,
        'info_box': args.info_box,
        'verbose': args.verbose,
    }

    images = load_images(args.folder)
    total_images = len(images)
    collage_groups = [images[i:i + params['pics_per_page']] for i in range(0, total_images, params['pics_per_page'])]

    start_time = time.time()

    print("Generating collages...")
    for idx, group in enumerate(collage_groups):
        print(f"Generating collage {idx + 1}...")
        create_collage(group, idx + 1, params['width'], params['height'], params, verbose=params['verbose'])
    print("Collage generation complete.")

    end_time = time.time()
    time_elapsed = end_time - start_time
    print(f"Total time taken: {time_elapsed:.2f} seconds")


if __name__ == "__main__":
    main()
       
