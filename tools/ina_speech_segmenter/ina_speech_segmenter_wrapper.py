#!/usr/bin/env python3

import os
import os.path
import shutil
import subprocess
import sys
import tempfile


def main():
	(input_file, json_file) = sys.argv[1:3]
	
	with tempfile.TemporaryDirectory() as tmpdir:
		temp_input_file = f"{tmpdir}/xxx.wav"
		temp_output_file = f"{tmpdir}/xxx.json"
		shutil.copy(input_file, temp_input_file)

		r = subprocess.run(["singularity run", "/srv/amp/ina-speech-tools-singularity/ina-speech-tools-singularity.sif", temp_input_file, temp_output_file])
        
		shutil.copy(temp_output_file, json_file)

		if os.path.exists(temp_input_file):
			os.remove(temp_input_file)

		if os.path.exists(temp_output_file):
			os.remove(temp_output_file)
		
	exit(r.returncode)
		
if __name__ == "__main__":
	main()
