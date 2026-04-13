input=$1
input="${input%.*}" # strip extention

# ffmpeg -i ${input}.mp3 -filter_complex "ebur128=hop=10" -f null - 2> ${input}.txt
ffmpeg -i ${input}.mp3 -filter_complex "asetnsamples=n=480,ebur128=metadata=1" -f null - 2> ${input}.txt
