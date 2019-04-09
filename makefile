targets=client server har-server har-client
bins=$(patsubst %,bin/%,$(targets))

default: force sync

all : $(bins)

clean :
	rm -f $(bins)

force: clean all

sync:
	rsync -avz --delete ./ mininet-vm:~/sync/

bin/% : src/%
	GOOS=linux GOARCH=amd64 go build -o $@ ./$<

.PHONY : default clean force all sync
