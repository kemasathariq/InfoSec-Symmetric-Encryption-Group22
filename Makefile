.PHONY: install test bench bench-quick analyze
install:
	pip install -r requirements.txt
test:
	python -m pytest kcrypto -q
bench-quick:        # smoke test ~1 menit, BUKAN hasil untuk laporan
	python -m bench.harness run --quick && python -m bench.analyze
bench:              # hasil untuk laporan: tutup aplikasi lain, colok charger
	python -m bench.harness run --reps 30 --big-reps 10 --video-mb 100 && python -m bench.analyze
analyze:
	python -m bench.analyze
