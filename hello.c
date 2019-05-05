// #include <stdio.h>

//int y = 88;

int func1(int x)
{
	printf("Hello Ker! func1: x=%d\n", x);
    int i = x + 1;
    int max = 6;
	if (i == max) {
		return 99;
	} else {
		return func1(i);
	}
    return 88;
}


int main()
{
    int x = 0;
    int y = func1(x);
    printf("Hello Ker! main: x=%d, y=%d\n", x, y);
    return 0;
}
