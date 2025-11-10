import base64
import os

def gen_tile_list():
    output = []

    directory = "C:/Users/kayp/Documenten/OpenJournals/Tijdschriften/erlacs/iles/RE_ New Upload ERLACS"
    
    # Check if directory exists
    if not os.path.exists(directory):
        print(f"Directory does not exist: {directory}")
        return output
    
    for tile in os.scandir(directory):
        if tile.is_file():
            try:
                # Use tile.path to get the full file path
                with open(tile.path, 'rb') as f:  # Open in binary mode
                    file_content = f.read()  # Read the file content
                    encoded_content = base64.b64encode(file_content)  # Encode the content
                    output.append(encoded_content.decode('utf-8'))
            except Exception as e:
                print(f"Error processing file {tile.name}: {e}")
                continue

    print(f"Processed {len(output)} files")
    return output