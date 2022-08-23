import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('target', help='Source file to convert to pdf')
    parser.add_argument('-r', help='recursively process files in a directory to pdf', default = False)
    args = parser.parse_args()
    print("Hello! It's Mora time!")