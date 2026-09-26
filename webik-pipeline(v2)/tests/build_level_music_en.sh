#!/usr/bin/env bash
# EN «Iceberg DreamWorks» (Debik): те же 4 ностальгия-трека, перелуп под EN-длины + даккинг под EN-голос.
# EN-границы: L2=08:00(480.1) L3=16:06(965.9) L4=24:04(1443.7), всего 33:47(2027.2).
set -e
RU="projects/2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"
EN="${RU}_EN"
M="$EN/assets/music"; SRC="$RU/assets/music"
VOICE="$EN/assets/voice/full.mp3"
mkdir -p "$M"

L1="$SRC/dw_L1_gloss.mp3";   S1=485
L2="$SRC/dw_L2_buried.mp3";  S2=491
L3="$SRC/dw_L3_machine.mp3"; S3=483
L4="$SRC/dw_L4_abyss.mp3";   S4=589

echo "=== луплю сегменты ==="
ffmpeg -y -loglevel error -stream_loop -1 -i "$L1" -t $S1 "$M/_s1.mp3"
ffmpeg -y -loglevel error -stream_loop -1 -i "$L2" -t $S2 "$M/_s2.mp3"
ffmpeg -y -loglevel error -stream_loop -1 -i "$L3" -t $S3 "$M/_s3.mp3"
ffmpeg -y -loglevel error -stream_loop -1 -i "$L4" -t $S4 "$M/_s4.mp3"

echo "=== склейка кроссфейдами (5с) ==="
ffmpeg -y -loglevel error -i "$M/_s1.mp3" -i "$M/_s2.mp3" -i "$M/_s3.mp3" -i "$M/_s4.mp3" \
  -filter_complex "[0][1]acrossfade=d=5:c1=tri:c2=tri[a];[a][2]acrossfade=d=5:c1=tri:c2=tri[b];[b][3]acrossfade=d=5:c1=tri:c2=tri[c]" \
  -map "[c]" "$M/_levels_chain.mp3"
echo "chain: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$M/_levels_chain.mp3")с"

echo "=== ДАККИНГ под EN-голос + -20 LUFS + фейды ==="
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$M/_levels_chain.mp3")
FO=$(python -c "print(max(0,float('$DUR')-4))")
ffmpeg -y -loglevel error -i "$M/_levels_chain.mp3" -i "$VOICE" \
  -filter_complex "[0:a]aformat=sample_rates=48000:channel_layouts=stereo[m];[1:a]aformat=sample_rates=48000:channel_layouts=stereo,apad[s];[m][s]sidechaincompress=threshold=0.04:ratio=8:attack=15:release=600:makeup=1:level_sc=0.9[d];[d]loudnorm=I=-20:TP=-2,afade=t=in:st=0:d=4,afade=t=out:st=$FO:d=4[out]" \
  -map "[out]" -t "$DUR" "$M/bg_bed_levels.mp3"
echo "ГОТОВО bg_bed_levels.mp3: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$M/bg_bed_levels.mp3")с"
rm -f "$M"/_s1.mp3 "$M"/_s2.mp3 "$M"/_s3.mp3 "$M"/_s4.mp3 "$M"/_levels_chain.mp3
