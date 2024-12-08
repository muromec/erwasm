
%.S: %.erl
	erlc -S $<

%.wat: %.S
	python ./erwasmc.py $< $@

%.wasm: %.wat
	wasm-tools parse $< -o $@

beam_parser.py: beam.g
	python -m lark.tools.standalone -s module $< -o $@

run: simple.wasm listdemo.wasm
	node run.js simple.wasm
	# node run.js listdemo.wasm
