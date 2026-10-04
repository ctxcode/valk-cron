vc ?= valk

test:
	$(vc) build ./tests --test --run
lint:
	$(vc) build ./src --lint
example:
	$(vc) build ./example --run
bench:
	$(vc) build ./bench -o bench/bench --release && ./bench/bench
docs:
	$(vc) doc . -o docs/api.md --markdown --no-private
	$(vc) doc . -o docs/api-full.md --markdown --no-private --full

.PHONY: test lint example bench docs
