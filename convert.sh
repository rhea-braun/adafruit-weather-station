for f in *.bmp; do 
    [[ "$f" == *"_small.bmp" ]] && continue
    magick "$f" -resize 20x20 -colorspace gray -type palette -compress none "${f%.bmp}_small.bmp"
done