#!/bin/bash

# Set base directory
SCRIPT_DIR="$(dirname "$0")"
INPUT_DIR="$SCRIPT_DIR/input"

# Repositories to clone
KEYWORDS_REPO="https://github.com/SDuari/Keyword-Extraction-Datasets.git"
ACOS_REPO="https://github.com/yangheng95/ABSADatasets.git"

# Destination folders
KEYWORDS_DIR="$INPUT_DIR/Keywords"
ACOS_DIR="$INPUT_DIR/ACOS"

# Function to clone or update a repository
clone_or_update_repo() {
    local repo_url="$1"
    local target_dir="$2"

    if [[ -d "$target_dir/.git" ]]; then
        echo "Updating repository: $target_dir"
        git -C "$target_dir" pull
    else
        echo "Cloning repository: $repo_url into $target_dir"
        git clone --depth 1 "$repo_url" "$target_dir"
    fi
}

####### CLONE KEYWORDS REPOSITORY #######
clone_or_update_repo "$KEYWORDS_REPO" "$KEYWORDS_DIR"

####### PROCESS ZIP FILES #######
echo "Processing ZIP files in the Keywords repository..."

find "$KEYWORDS_DIR" -maxdepth 1 -type f -name "*.zip" | while read ZIP_FILE_PATH; do
    ZIP_NAME=$(basename "$ZIP_FILE_PATH" .zip)
    ZIP_DEST_DIR="$KEYWORDS_DIR/$ZIP_NAME"

    # Skip extraction if folder already exists
    if [[ -d "$ZIP_DEST_DIR" ]]; then
        echo "Skipping extraction: $ZIP_NAME already exists."
        continue
    fi

    mkdir -p "$ZIP_DEST_DIR"
    echo "Extracting $ZIP_FILE_PATH to $ZIP_DEST_DIR"
    unzip -o "$ZIP_FILE_PATH" -d "$ZIP_DEST_DIR"

    rm "$ZIP_FILE_PATH"
done

####### CLONE ACOS DATASET REPOSITORY #######
TEMP_ACOS_DIR="$INPUT_DIR/ABSADatasets_temp"
clone_or_update_repo "$ACOS_REPO" "$TEMP_ACOS_DIR"

# Ensure the ACOS dataset directory exists
mkdir -p "$ACOS_DIR"

# Verify the expected folder structure
ACOS_SRC="$TEMP_ACOS_DIR/datasets/acos_datasets"

if [[ ! -d "$ACOS_SRC" ]]; then
    echo "ERROR: acos_dataset folder not found in repository at expected location."
    echo "Checking repository contents..."
    ls -R "$TEMP_ACOS_DIR"  # Debugging: Show repo structure
    exit 1
fi

# Move only the 'acos_dataset' subfolders if they don't already exist
echo "Moving acos_dataset into $ACOS_DIR"
for dataset in "$ACOS_SRC"/*; do
    dataset_name=$(basename "$dataset")
    dataset_dest="$ACOS_DIR/$dataset_name"

    if [[ -d "$dataset_dest" ]]; then
        echo "Skipping dataset: $dataset_name already exists."
    else
        echo "Moving dataset: $dataset_name to $dataset_dest"
        mv "$dataset" "$dataset_dest"
    fi
done

# Cleanup the temporary repo
if [[ -d "$TEMP_ACOS_DIR" ]]; then
    echo "Cleaning up temporary repository..."
    rm -rf "$TEMP_ACOS_DIR"
fi

echo "All tasks completed!"
