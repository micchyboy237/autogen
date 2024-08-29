git reset
git remote add original git@github.com:microsoft/autogen.git
git fetch original
git checkout main
git merge original/main
git push origin main

# Run the following command to make the script executable
# chmod +x _jet_merge_main.sh
