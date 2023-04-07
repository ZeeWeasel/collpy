# Collpy

Collpy is a Python script that allows you to create customizable image collages from a folder of images. With options such as border, padding, alignment, text size, and more, you can easily generate a collage that suits your needs.

## Features

- Generate collages from a folder of images
- Customize border, padding, and alignment
- Adjust text size and opacity
- Add info box with date and parameters
- Command-line interface for easy usage

## Installation

1. Clone the repository:

```bash
git clone https://github.com/weaselinabox/collpy.git
```

2. Install the required package (Pillow):

```bash
pip install Pillow
```

3. Change into the repository directory:

```bash
cd collpy
```

## Usage

1. Place your images in the `images` folder.

2. Run the script with default settings:

```bash
python collpy.py
```

3. To customize the collage, use command-line arguments as needed:

```bash
python collpy.py -w 6600 -h 5100 --padding 10 --align left --text-size 24 --text-opacity 0.8 --date-format '%Y-%m-%d' --prefix collage --bg-color 255,255,255 --info-box
```

For a full list of command-line arguments and their descriptions, run:

```bash
python collpy.py --help
```

## License

MIT License
