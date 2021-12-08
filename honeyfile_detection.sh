#!/usr/bin/env bash

root_folder=$1
sudo /usr/bin/python3 create_honeyfiles.py --root $root_folder

case $root_folder in
    /*)
        ;;
    ./*)
        cwd_variable=$(pwd)
        root_folder=${root_folder:2}
        root_folder="${cwd_variable}/${root_folder}"
        ;;
    *)
        cwd_variable=$(pwd)
        root_folder="${cwd_variable}/${root_folder}"
        ;;
esac

case $root_folder in
    */)
        honey_fname="${root_folder}.honey1.pdf"
        ;;
    *)
        honey_fname="${root_folder}/.honey1.pdf"
        ;;
esac

sudo chmod 777 $honey_fname

for d in $(find $root_folder -type d)
do
    if [ "$d" == "$root_folder" ]; then
        continue
    fi
    case $d in 
    */)
        sudo ln -s $honey_fname "${d}.honey1.pdf"
        ;;
    *)
        sudo ln -s $honey_fname "${d}/.honey1.pdf"
        ;;
    esac 
done

sudo service auditd start
sudo auditctl -D
sudo auditctl -w $honey_fname -p war -k user1

while inotifywait -q -e access,attrib,open,modify $honey_fname; do
    echo "IN LOOP"
    pid_this=$(sudo ausearch -f $honey_fname | more | grep -o ' pid=[0-9]* ' | grep -v 'grep' | sed 's/\ pid=//' | tail -1 | tr '\n' ' ')
    # pid_this=$(lsof $honey_fname | awk 'NR==2 {print $2}')
    
    if [ "$pid_this" ]; then
        echo ${pid_this}
        inotifywait -q -e close $honey_fname
        kill -STOP ${pid_this}
        echo "CRITICAL: A program tried to access a honey file and was suspended. Running checks."
        
        if ! [ -f $honey_fname ]; then
            kill -9 ${pid_this}
            sudo chmod -R 400 $root_folder
            echo "CRITICAL: The program overwrote the honey file and was killed. Permissions of folder set to read only."
            break
        else
            python2 driver.py $honey_fname
            varDriver=$(cat .meanEntropy.txt)
            num2=7.5
            echo "HOPEFULLY this is the mean from driver"
            echo "$varDriver"
            if (( $(echo "$varDriver > $num2" |bc -l) )); then
                echo "Should be encryption value (greater)"
            else
                echo "Not encryption (lesser)"
            fi
        fi
        kill -CONT ${pid_this}
    fi
done




