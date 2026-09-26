#!/usr/bin/env bash
# «Айсберг Reddit»: крипи-цифровой саспенс по 4 уровням (поверхность → крипипаста → шифры/ARG → бездна) + даккинг.
# Границы: L2=374s L3=721s L4=1097s, голос ~1548s.
set -e
P="projects/2026-09-13_aysberg-reddit-strannaya-i-trevozhnaya-storona"
M="$P/assets/music"
VOICE="$P/assets/voice/full.mp3"

L1="$M/reddit_L1_surface.mp3"; S1=379
L2="$M/reddit_L2_horror.mp3";  S2=352
L3="$M/reddit_L3_cipher.mp3";  S3=381
L4="$M/reddit_L4_abyss.mp3";   S4=461

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

echo "=== ДАККИНГ: сайдчейн от голоса + -20 LUFS + фейды ==="
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$M/_levels_chain.mp3")
FO=$(python -c "print(max(0,float('$DUR')-4))")
ffmpeg -y -loglevel error -i "$M/_levels_chain.mp3" -i "$VOICE" \
  -filter_complex "[0:a]aformat=sample_rates=48000:channel_layouts=stereo[m];[1:a]aformat=sample_rates=48000:channel_layouts=stereo,apad[s];[m][s]sidechaincompress=threshold=0.04:ratio=8:attack=15:release=600:makeup=1:level_sc=0.9[d];[d]loudnorm=I=-20:TP=-2,afade=t=in:st=0:d=4,afade=t=out:st=$FO:d=4[out]" \
  -map "[out]" -t "$DUR" "$M/bg_bed_levels.mp3"
echo "ГОТОВО bg_bed_levels.mp3: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$M/bg_bed_levels.mp3")с ($(du -k "$M/bg_bed_levels.mp3"|cut -f1)KB)"
rm -f "$M"/_s1.mp3 "$M"/_s2.mp3 "$M"/_s3.mp3 "$M"/_s4.mp3 "$M"/_levels_chain.mp3
