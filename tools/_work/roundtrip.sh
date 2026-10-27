cd /d/APP/SRC/laragon/www/itel-watchface/tools
for f in ../cache/JL/AM05/default/category/*/*.bin; do id=$(basename $f .bin)
python -I wfunpack.py $f _work/u_$id >/dev/null && python -I wfpack.py _work/u_$id _work/rt_$id.bin >/dev/null
a=$(sha256sum < $f | cut -c1-16); b=$(sha256sum < _work/rt_$id.bin | cut -c1-16)
[ "$a" = "$b" ] && r=OK || r=DIFF; echo "$id $(stat -c%s $f) $a $b $r"; done
