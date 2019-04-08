targets=client server har-server
bins=$(patsubst %,bin/%,$(targets))

default : $(bins)

clean :
	rm -f $(bins)

force: clean default

bin/% : src/%
	GOOS=linux GOARCH=amd64 go build -o $@ ./$<

.PHONY : default clean force
