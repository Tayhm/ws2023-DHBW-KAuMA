#!/bin/bash
for i in {1..3}
do
if ! [ $i -eq 1 ]
then
    echo "$out"
fi
out=""
if [ $i -eq 1 ]
then

    for j in {1..7}
    do

        out="$out$(../kauma "testcases/2.3_ct${i}_block${j}.json")"

    done

elif [ $i -eq 2 ]
then

    for j in {1..13}
    do
        out="$out$(../kauma "testcases/2.3_ct${i}_block${j}.json")"
    done

else

    for j in {1..5}
    do
        out="$out$(../kauma "testcases/2.3_ct${i}_block${j}.json")"
    done

fi

done

echo "$out"