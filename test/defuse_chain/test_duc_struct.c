#include <stdio.h>


typedef struct {
  char name[50];
  int citNo;
  float salary;
} Person;

int main(char argc) {
    Person person1;
    int c = 5;
    
    // assign values to other person1 variables
    person1.salary = 2500;
    person1.citNo = person1.salary = 1984;
    int b = person1.salary + c;

    if (b > 0) {
        return b;
    } else {
        return person1.salary;
    }
}
