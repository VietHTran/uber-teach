#!/bin/bash
#Use: auto commit to remote repository

read -p "Do you want to proceed, sir? [Y/N]" option
declare -l isProceed=$option
if [[ $isProceed == "n" || $isProceed == "no" || $isProceed == "nein" ]]
then
	echo "Commit abort"
	exit 1
fi


#Initialize extension dictionary, allow user to choose which file types to commit
declare -A addEx
function watch {
	addEx["$1"]="0"
}

function initdict {
	watch "py"
	watch "css"
	watch "js"
	watch "html"
	watch "sh"
}

#Check file's extension
function check {
	#echo -e "\tFile: $1" #debug
	filename=$(basename "$1")
	extension="${filename##*.}"
	#echo -e "\tExtension: $extension" #debug
	if [ -n $extension ] && [ -n "${addEx[$extension]}" ]; then
		echo -e "\tAdd file: $1" #debug
		git add "$1"
	fi
}

#Automatically add untracked files to staging area
function autoadd {
	#display a list of untracked files
	git clean --dry-run | awk '{print $3;}' |
		while read -r fullFileName; do
			check "$fullFileName"
		done
	git ls-files --others --exclude-standard |
		while read -r fullFileName; do
			check "$fullFileName"
		done
}

initdict
autoadd
#exit 1; #debug

read -p "Commit message: " title
if [ -z "$title" ]; then
	title="{{No title}}"
fi

git commit -am "$title"
git push
