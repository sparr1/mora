def parse_position(pos_string):
    return pos_string.replace('(', '').replace(')', '').split(',')

# Function to parse attributes from a line
def parse_attributes(line):
    attributes = line[line.index('[')+1:line.index(']')].split(', ')
    parsed_attributes = {}
    for attr in attributes:
        key, value = attr.split('=')
        if key == 'pos':
            value = parse_position(value)
        parsed_attributes[key] = value
    return parsed_attributes

def resolve_relative_dimensions(width, height, page_width, page_height):
    # Function to resolve relative dimension tags to absolute values
    def resolve_dimension(dim, total_size):
        # Handle relative tags
        if dim == '%half':
            return total_size / 2
        elif dim == '%quarter':
            return total_size / 4
        elif dim == '%eighth':
            return total_size / 8
        elif dim == '%sixteenth':
            return total_size / 16
        elif dim.endswith('in'):
            # Handle inches
            return float(dim[:-2]) * 72  # 1 inch = 72 points in PDF
        else:
            # Handle raw PDF format (72nds of an inch)
            return float(dim)

    # Resolve width and height
    resolved_width = resolve_dimension(width, page_width)
    resolved_height = resolve_dimension(height, page_height)

    return resolved_width, resolved_height

def resolve_relative_position(pos, page_width, page_height, box_width, box_height):
    # Function to resolve relative position tags to absolute values
    vertical, horizontal = pos
    x, y = 0, 0

    if vertical == '%top':
        y = 0
    elif vertical == '%mid':
        y = (page_height - box_height) / 2
    elif vertical == '%bot':
        y = page_height - box_height

    if horizontal == '%left':
        x = 0
    elif horizontal == '%mid':
        x = (page_width - box_width) / 2
    elif horizontal == '%right':
        x = page_width - box_width

    return x, y

# Function to parse the .mora file
def parse_mora_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    pages = []
    page_stack = []  # Stack to keep track of pages
    box_stack = []  # Stack to keep track of nested boxes
    for line in lines:
        line = line.strip()
        if line.startswith('@page['):
            # Start a new page with attributes
            attributes = parse_attributes(line)
            page = {'attributes': attributes, 'boxes': []}
            page_stack.append(page)
        elif line.startswith('@box['):
            # Start a new box with attributes
            attributes = parse_attributes(line)
            box = {'attributes': attributes, 'content': []}
            if box_stack:
                box_stack[-1]['content'].append(box)
            else:
                page_stack[-1]['boxes'].append(box)
            box_stack.append(box)
        elif line == '@endbox':
            box_stack.pop()
        elif line == '@endpage':
            # End the current page and add it to the pages list
            page = page_stack.pop()
            pages.append(page)
        elif line and box_stack:
            # Add content to the current box
            box_stack[-1]['content'].append(line)

    for page in pages:
        # Retrieve page attributes
        # Convert page attributes from inches to PDF units
        page['attributes']['width'] = float(page['attributes']['width'].strip('in')) * 72
        page['attributes']['height'] = float(page['attributes']['height'].strip('in')) * 72
        page['attributes']['margin'] = float(page['attributes']['margin'].strip('in')) * 72

        # Retrieve page attributes
        page_width = page['attributes']['width']
        page_height = page['attributes']['height']

        for box in page['boxes']:
            # Resolve width and height
            resolved_width, resolved_height = resolve_relative_dimensions(
                box['attributes']['width'], box['attributes']['height'], page_width, page_height)

            # Resolve position
            resolved_x, resolved_y = resolve_relative_position(
                box['attributes']['pos'], page_width, page_height, resolved_width, resolved_height)

            # Update box attributes with absolute values
            box['attributes']['pos'] = (resolved_x, resolved_y)
            box['attributes']['width'] = resolved_width
            box['attributes']['height'] = resolved_height

    return pages        

if __name__ == '__main__':
    pages = parse_mora_file('struct_text.mora')
    print(pages)
