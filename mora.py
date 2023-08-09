import argparse
from parser import parse_mora_file
import traceback
import sys
import os

def minimal_header():
    head = b'%PDF-1.1\n'
    head += bytes('%¥±ë\n','utf-8')
    return head

def setup_indirect_obj(obj_type, size, n, length = -1):
    obj_string = bytes(''+str(n)+' 0 obj\n', 'utf-8')
    if obj_type == 'stream':
        assert(length > 0)
        obj_string += bytes(' << /Length '+str(length)+ ' >>\n', 'utf-8')
        obj_string += b'stream\n'
        obj_string += b'  BT\n'
    else:
        obj_string += bytes('  << /Type /' + obj_type+'\n', 'utf-8')
    return obj_string

def teardown_indirect_obj(obj_string, n, obj_type = "object"):
    if obj_type == "stream":
        obj_string += b'  ET\n'
        obj_string += b'endstream\n'
        obj_string += b'endobj\n'
    else:
        obj_string += b'  >>\n'
        obj_string += b'endobj\n'
    return n+1, obj_string

def minimal_catalog(size = 0, Pages_index = 2,  n=1):
    catalog = setup_indirect_obj("Catalog", size, n)
    catalog += bytes('     /Pages'+' '+str(Pages_index)+' 0 R\n', 'utf-8')
    return teardown_indirect_obj(catalog, n)

def minimal_pages(size = 0, n=1):
    pages = setup_indirect_obj("Pages",size,n)
    pages += b'     /Kids [3 0 R]\n'
    pages += b'     /Count 1\n'
    pages += b'     /Mediabox [0 0 300 144]\n'
    return teardown_indirect_obj(pages,n)

def minimal_page(size = 0, n = 1):
    page = setup_indirect_obj("Page", size, n)
    page += b'     /Parent 2 0 R\n'
    page += b'     /Resources\n'
    page = add_font(page, 'Type1', 'Times-Roman', 1)
    page += b'     /Contents 4 0 R\n'
    return teardown_indirect_obj(page, n)

def add_font(page_so_far, subtype, base_font, nth_font):
    page_so_far +=      b'      << /Font\n'
    page_so_far += bytes('          << /F'+str(nth_font)+'\n', 'utf-8')
    page_so_far +=      b'              << /Type /Font\n'
    page_so_far += bytes('                 /Subtype /'+subtype+'\n','utf-8')
    page_so_far += bytes('                 /BaseFont /'+base_font+'\n','utf-8')
    page_so_far +=      b'              >>\n'
    page_so_far +=      b'          >>\n'
    page_so_far +=      b'      >>\n'
    return page_so_far


def minimal_stream(input_strs, size = 0, n = 1, x_offset=180, y_offset=600):
    stream  = setup_indirect_obj("stream",size = size,n=n,length=102)
    initial_bytes = len(stream)
    stream +=      b'    /F1 18 Tf\n'
    stream +=      b'    18 TL\n'  # Set leading (vertical distance between lines)
    stream += bytes(f'    {x_offset} {y_offset} Td\n', 'utf-8')  # Set initial position
    for input_str in input_strs:
        stream += bytes('('+input_str+') Tj\n','utf-8')
        stream += b'    T*\n'  # Move to next line

    corrected_byte_count = 10 + len(stream) - initial_bytes
    print("message byte count", corrected_byte_count)

    return corrected_byte_count, teardown_indirect_obj(stream, n, obj_type="stream")

def gen_xref(data_so_far, size, n):
    new_pos = 457 + data_so_far
    xref = b'xref\n'
    xref += bytes(str(size)+' '+ str(n)+'\n','utf-8')
    xref += b'0000000000 65535 f\n'
    xref += b'0000000018 00000 n\n'
    xref += b'0000000077 00000 n\n'
    xref += b'0000000178 00000 n\n'
    xref += bytes('0000000' +str(new_pos) +' 00000 n\n','utf-8')
    return n, xref

def minimal_trailer(n):
    trailer  =      b'trailer\n'
    trailer +=      b'  <<  /Root 1 0 R\n'
    trailer += bytes('      /Size '+str(n) +'\n','utf-8')
    trailer +=      b'  >>\n'
    return trailer

def end_of_file(xref_bytes):
    eof  =      b'startxref\n'
    eof += bytes(str(xref_bytes)+'\n','utf-8')
    eof +=      b'%%EOF'
    return eof

def process(file):
    try:
        f = open(file,'r')
        print("Starting to process", file,'...')
        filename, file_extension = os.path.splitext(file)
        print(file_extension)
        assert(file_extension[1:] in ['mora', 'mor', 'MORA', 'MOR'])
        lines = f.readlines()
        print(lines)
    except Exception as err:
        print("Had some trouble opening", args['target'],'... likely wrong filename or directory.')
        print(traceback.format_exc())
        sys.exit()
    finally:
        f.close()
    # print(lines)
    try:
        target_file = filename + '.pdf'
        print("Writing results to file", target_file,'...')

        p = open(target_file,'wb')

        header = minimal_header()
        p.write(header + b'\n')
        n, catalog = minimal_catalog()
        p.write(catalog+b'\n')
        n, pages = minimal_pages(n=n)
        p.write(pages+b'\n')
        n, page = minimal_page(n=n)
        p.write(page+b'\n')
        text_bytes, (n, stream) = minimal_stream(lines,n=n)
        byte_adjust = (text_bytes-55)

        p.write(stream+b'\n')
        n, xref = gen_xref(byte_adjust,0, n)
        p.write(xref)
        trailer = minimal_trailer(n)
        p.write(trailer)
        eof = end_of_file(565 + byte_adjust)
        p.write(eof+b'\n')

        print("Done!")
    except Exception as err:
        print(traceback.format_exc())
    finally:
        p.flush()
        sys.exit()

def process_dir(dir):
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('target', help='Source file to convert to pdf')
    parser.add_argument('-r', help='recursively process files in a directory to pdf', action='store_true')
    args = vars(parser.parse_args())
    print("Hello! It's Mora time!")
    if args['r']:
        process_dir(args['target'])
    else:
        process(args['target'])
    # f = open('args[0]')
