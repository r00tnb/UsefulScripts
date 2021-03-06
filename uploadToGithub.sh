#!/bin/bash

# $1 is file path
filepath=${1:?"A file path must be given."}
if [ ! -f $filepath ];then
    echo -e "The file: $filepath\n\t is not exists or not a file."
    exit
elif [ ! -r $filepath ];then
    echo -e "The file: $filepath\n\t is not readable."
    exit
elif [[ `ls -l $filepath | awk '{print $5}'` -gt 1024*1024*1024 ]];then
    echo -e "The file: $filepath\n\t size of file over 1GB."
    exit
else
    echo "Good file!File size: "`ls -lh $filepath | awk '{print $5}'`
fi

# $2 is git repository url
repo=${2:-"https://github.com/r00tnb/uploadTools.git"}

# $3 is username
username=${3:-"r00tnb"}

# $4 is email
email=${4:-"1912971419@qq.com"}

read -p "This script will cover the repo $repo."$'\n'"Are you sure to continue?(y/n)" yesno
if [ $yesno != "y" ];then
    exit
fi

mkdir uploadFileToGithub
cp $filepath uploadFileToGithub/
cd uploadFileToGithub
filepath=${filepath##*/}

git init
git config --local user.name "$username"
git config --local user.email "$email"
git remote add origin $repo
git config --local credential.helper cache
git config --local http.postBuffer 1073741824

cat>resume.sh<<EOF
#!/bin/bash
# upload a file:$filepath

cat dir_*/* > $filepath
EOF
cat>resume.bat<<EOF
rem upload a file:$filepath

copy /b dir_*\* $filepath
EOF
git add resume.sh resume.bat
git commit -m "add resume.sh and resume.bat"
git push -f origin master

# split file
# every upload size
uploadsize="80m"
minimizesize="10m"

split -b $uploadsize $filepath myfile

for file in myfile*
do
    mkdir "dir_"$file
    mv $file "dir_$file/"
    cd "dir_$file/"
    split -b $minimizesize $file upfile
    rm -f $file
    git add upfile*
    git commit -m "$file upload"
    git push origin master
    cd ..
done
