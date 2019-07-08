for f in dissertation_refs/*.txt
do
    python app.py -text $f -save
done