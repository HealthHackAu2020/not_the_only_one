#!/bin/bash

for file in group_1 group_2; do
	for dim in 40 60 58 87 80 120 180 20 29 76 152 167 1024; do
		inkscape --export-filename="${file}_${dim}.png" -w ${dim} ${file}.svg
		convert ${file}_${dim}.png -gravity center -extent ${dim}x${dim} ${file}_${dim}x${dim}.png	
	done
done

