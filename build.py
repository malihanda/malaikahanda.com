import os
import json
import random
import shutil

import yaml

from jinja2 import Environment, FileSystemLoader, select_autoescape
import markdown2
from PIL import Image, ImageDraw, ImageColor

# Configuration
CONFIG_FILE = 'config.yaml'
TEMPLATE_DIR = 'templates'
INDEX_TEMPLATE_NAME = 'index.html.jinja'
CSS_SRC_DIR = 'styles' # Source directory for CSS template
CSS_TEMPLATE_NAME = 'styles.css' # Name of your CSS template
DATA_FILE = 'data.json'
OUTPUT_DIR = '_site'
STATIC_DIRS = ['js', 'assets'] 
STATIC_FILES = [DATA_FILE, 'og-image.png']
FAVICON_OUTPUT_DIR = OUTPUT_DIR

def generate_favicons(colors, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    base_size = 64
    img = Image.new('RGB', (base_size, base_size))
    draw = ImageDraw.Draw(img)
    quad_size = base_size // 2

    draw.rectangle([0, 0, quad_size, quad_size], fill=colors['color-2'])
    draw.rectangle([quad_size, 0, base_size, quad_size], fill=colors['color-3'])
    draw.rectangle([0, quad_size, quad_size, base_size], fill=colors['color-4'])
    draw.rectangle([quad_size, quad_size, base_size, base_size], fill=colors['color-1'])

    sizes_png = {
        "favicon-16x16.png": 16,
        "favicon-32x32.png": 32,
        "apple-touch-icon.png": 180,
        "android-chrome-192x192.png": 192,
    }
    for filename, size in sizes_png.items():
        resized_img = img.resize((size, size), Image.Resampling.NEAREST)
        resized_img.save(os.path.join(output_dir, filename))
        print(f"Generated {filename} ({size}x{size})")
    
    try:
        img_16 = img.resize((16,16), Image.Resampling.NEAREST)
        img_32 = img.resize((32,32), Image.Resampling.NEAREST)
        img_48 = img.resize((48,48), Image.Resampling.NEAREST)
        ico_path = os.path.join(output_dir, "favicon.ico")
        img_16.save(ico_path, append_images=[img_32, img_48])
        print(f"Generated high-quality favicon.ico with 16x16, 32x32, 48x48")
    except Exception as e:
        print(f"Could not generate high-quality favicon.ico: {e}.")

def generate_og_image(colors):
    img_width = 1200
    img_height = 630

    cell_fill_colors = [
        colors['color-1'], 
        colors['color-2'], 
        colors['color-3'], 
        colors['color-4']
    ]
    background_color = colors['background']

    img = Image.new('RGB', (img_width, img_height), color=ImageColor.getrgb(background_color))
    draw = ImageDraw.Draw(img)

    cell_size = 30
    cell_gap = 10
    radius = 4

    y = int(-cell_size * 0.5)
    while y < img_height:
        x = int(-cell_size * 0.5)
        while x < img_width:
            fill_color = random.choice(cell_fill_colors)
            
            draw.rounded_rectangle(
                [x, y, x + cell_size, y + cell_size], 
                fill=ImageColor.getrgb(fill_color), 
                radius=radius
            )
            x += cell_size + cell_gap
        y += cell_size + cell_gap

    og_image_path = "og-image.png"
    img.save(og_image_path)
    print(f"Generated OG image: {og_image_path}")

def markdown_filter(value):
    return markdown2.markdown(value, extras=["target-blank-links"])

def main():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

    # Load configuration
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
        crossword_count = len([record for record in data if record.get('category') == 'puzzle'])
        
        if 'bio' in config and 'intro' in config['bio']:
            config['bio']['intro'] = config['bio']['intro'].format(crossword_count=str(crossword_count))

    # Extract theme colors for favicon and CSS processing
    theme_colors = config['theme_colors']

    print(f"Using theme colors: {theme_colors}")

    generate_favicons(theme_colors, FAVICON_OUTPUT_DIR)
    if not os.path.exists('og-image.png'):
        generate_og_image(theme_colors)

    html_env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(['html'])
    )
    html_env.filters['markdown'] = markdown_filter

    css_env = Environment(
        loader=FileSystemLoader(CSS_SRC_DIR),
        autoescape=select_autoescape([])
    )

    # Render the main HTML template
    index_template = html_env.get_template(INDEX_TEMPLATE_NAME)
    output_html = index_template.render(config=config)
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(output_html)
    print(f"Rendered index.html")

    # Process and render the CSS template
    try:
        css_template = css_env.get_template(CSS_TEMPLATE_NAME)
        output_css = css_template.render(theme_colors=theme_colors) 
        os.makedirs(os.path.join(OUTPUT_DIR, 'styles'))
        with open(os.path.join(OUTPUT_DIR, 'styles', 'styles.css'), 'w', encoding='utf-8') as f:
            f.write(output_css)
        print(f"Rendered styles/styles.css with theme colors")
    except Exception as e:
        print(f"Error processing CSS template: {e}")

    # Copy other static files and data.json
    for static_dir in STATIC_DIRS:
        if os.path.exists(static_dir):
            shutil.copytree(static_dir, os.path.join(OUTPUT_DIR, static_dir))
        else:
            print(f"Warning: Static directory '{static_dir}' not found.")

    for static_file in STATIC_FILES:
        if os.path.exists(static_file):
            shutil.copy(static_file, os.path.join(OUTPUT_DIR, os.path.basename(static_file)))
        else:
            print(f"Warning: Static file '{static_file}' not found.")

    print(f"Site built successfully in '{OUTPUT_DIR}' directory.")

if __name__ == '__main__':
    main() 