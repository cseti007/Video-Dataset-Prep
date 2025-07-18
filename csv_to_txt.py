import csv
import os
import re

def csv_to_text_files(csv_file_path, text_column, filename_column, output_directory="output_files"):
    """
    Reads a CSV file and creates separate text files for each row.
    
    Args:
        csv_file_path (str): Path to the input CSV file
        text_column (str): Name of the column containing text to save
        filename_column (str): Name of the column to use for filenames
        output_directory (str): Directory to save the text files
    """
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        print(f"Created output directory: {output_directory}")
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            if text_column not in reader.fieldnames:
                print(f"Error: Column '{text_column}' not found in CSV file.")
                print(f"Available columns: {', '.join(reader.fieldnames)}")
                return
            
            if filename_column not in reader.fieldnames:
                print(f"Error: Column '{filename_column}' not found in CSV file.")
                print(f"Available columns: {', '.join(reader.fieldnames)}")
                return
            
            files_created = 0
            
            for row_num, row in enumerate(reader, start=1):
                text_content = row[text_column] or ""
                filename_base = row[filename_column] or f"row_{row_num}"
                
                # Clean filename (remove invalid characters)
                filename_clean = re.sub(r'[<>:"/\\|?*]', '_', str(filename_base))
                filename_clean = filename_clean.strip()
                
                if not filename_clean:
                    filename_clean = f"row_{row_num}"
                
                # Check if filename ends with .mp4 and replace with .txt
                if filename_clean.lower().endswith('.mp4'):
                    filename_clean = filename_clean[:-4] + '.txt'  # Remove .mp4 and add .txt
                    print(f"Converted mp4 to txt: {filename_clean}")
                elif not filename_clean.lower().endswith('.txt'):
                    filename_clean = filename_clean + '.txt'  # Add .txt if no extension
                
                # Create full file path
                file_path = os.path.join(output_directory, filename_clean)
                
                # Handle duplicate filenames by adding a number
                counter = 1
                original_file_path = file_path
                while os.path.exists(file_path):
                    name, ext = os.path.splitext(original_file_path)
                    file_path = f"{name}_{counter}{ext}"
                    counter += 1
                
                # Write text content to file
                try:
                    with open(file_path, 'w', encoding='utf-8') as txtfile:
                        txtfile.write(text_content)
                    files_created += 1
                    print(f"Created: {file_path}")
                except Exception as e:
                    print(f"Error creating file {file_path}: {e}")
            
            print(f"\nCompleted! Created {files_created} text files in '{output_directory}' directory.")
            
    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file_path}' not found.")
    except Exception as e:
        print(f"Error reading CSV file: {e}")

if __name__ == "__main__":
    # Configuration
    CSV_FILE = "/home/cseti/Data/Datasets/videos/Wallace and Gromit/bestofall/style/1440x1024/captions/video_captions_refined.csv"
    TEXT_COLUMN = "triggered_caption"
    FILENAME_COLUMN = "path"
    OUTPUT_FOLDER = "/home/cseti/Data/Datasets/videos/Wallace and Gromit/bestofall/style/1440x1024/captions/txt"  # Define your output folder here

    
    # Run the function
    csv_to_text_files(CSV_FILE, TEXT_COLUMN, FILENAME_COLUMN, OUTPUT_FOLDER)


