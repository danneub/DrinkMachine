#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

const char * getfield(char* line,int num)
{
    char* found;

while(1)
{
    found = strsep(&line,",");
//    printf("%s  %08x\n",found,*found);
    if(!--num)
    {
       if (found[0] ==0)
       {
         
         return  "0";
       }
       else
       {
        return found;
       }
    }
}
}


int main()
{
	FILE* stream = fopen("recipes.csv","r");
	printf("Welcome to the recipe parser.\n");

        char line[1024];

        printf("MENU = {\n"); 
        while (fgets(line,1024, stream))
        {
           for(int i =0;line[i];i++)
            { line[i]=tolower(line[i]); }

           char * tmp = strdup(line);
           printf("  '%s': [\n",getfield(tmp,1));
           free (tmp);
           tmp = strdup(line);
           printf("    { 'bottle' : 0, 'proportion': %s },\n",getfield(tmp,2));
           free (tmp);
           tmp = strdup(line);
           printf("    { 'bottle' : 1, 'proportion': %s },\n",getfield(tmp,3));
           free (tmp);
           tmp = strdup(line);
           printf("    { 'bottle' : 2, 'proportion': %s },\n",getfield(tmp,4));
           free (tmp);
           tmp = strdup(line);
           printf("    { 'bottle' : 3, 'proportion': %s },\n",getfield(tmp,5));
           free (tmp);
           tmp = strdup(line);
           printf("    { 'bottle' : 4, 'proportion': %s },\n",getfield(tmp,6));
           free (tmp);
           tmp = strdup(line);
           printf("    { 'bottle' : 5, 'proportion': %s },\n",getfield(tmp,7));
           free (tmp);
           tmp = strdup(line);
           printf("    { 'bottle' : 6, 'proportion': %s },\n",getfield(tmp,8));
           free (tmp);
           tmp = strdup(line);
           printf("    { 'bottle' : 7, 'proportion': %s },\n",getfield(tmp,9));
           free (tmp);
           printf("  ],\n");
        }


}

