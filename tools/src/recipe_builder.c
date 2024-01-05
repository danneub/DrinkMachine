#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

char * getfield(char* line,int num,char* noValueString)
{
    char* found;

while(1)
{
    found = strsep(&line,",");
    //printf("%s  %08x\n",found,*found);
    if(!--num)
    {
       if (found[0] == 0  || found[0] == 0xd)
       {
         
         return  noValueString;
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
           printf("  '%s': [\n",getfield(tmp,1,"0"));
           free (tmp);
           tmp = strdup(line);
           printf("    { 'bottle' : 0, 'proportion': %s },\n",getfield(tmp,2,"0"));
           free (tmp);
           tmp = strdup(line);
           printf("    { 'bottle' : 1, 'proportion': %s },\n",getfield(tmp,3,"0"));
           free (tmp);
           tmp = strdup(line);
           printf("    { 'bottle' : 2, 'proportion': %s },\n",getfield(tmp,4,"0"));
           free (tmp);
           tmp = strdup(line);
           printf("    { 'bottle' : 3, 'proportion': %s },\n",getfield(tmp,5,"0"));
           free (tmp);
           tmp = strdup(line);
           printf("    { 'bottle' : 4, 'proportion': %s },\n",getfield(tmp,6,"0"));
           free (tmp);
           tmp = strdup(line);
           printf("    { 'bottle' : 5, 'proportion': %s },\n",getfield(tmp,7,"0"));
           free (tmp);
           tmp = strdup(line);
           printf("    { 'bottle' : 6, 'proportion': %s },\n",getfield(tmp,8,"0"));
           free (tmp);
           tmp = strdup(line);
           printf("    { 'bottle' : 7, 'proportion': %s },\n",getfield(tmp,9,"0"));
           free (tmp);
           tmp = strdup(line);
           printf("    { 'bottle' : 8, 'proportion': %s },\n",getfield(tmp,10,"0"));
           free (tmp);
           printf("  ],\n");
        }
        fclose(stream);
// -------------------  build alias dictionary  ------------- //
        char * returnString;
        char * tmp ;

	stream = fopen("recipes.csv","r");

        printf("MENU_ALIAS = {\n"); 
        while (fgets(line,1024, stream))
        {
           for(int i =0;line[i];i++)
           {
              line[i]=tolower(line[i]);
              if (line[i] == 0xd)line[i]=0;
           }

         for(int i=11;i<=14;i++)
         {
           tmp = strdup(line);
           returnString = getfield(tmp,i,"");
           if (returnString !="")
           {
              printf("     '%s': ",returnString);
              free (tmp);
              tmp = strdup(line);
              printf("  \"%s\" ,\n",getfield(tmp,1,"0"));
              free (tmp);
           }
         }
        }
        printf("}\n");
        fclose(stream);
// -------------------  build drink finish dictionary  ------------- //
	stream = fopen("recipes.csv","r");

        printf("MENU_GARNISH = {\n"); 
        while (fgets(line,1024, stream))
        {
           for(int i =0;line[i];i++)
           {
              line[i]=tolower(line[i]);
              if (line[i] == 0xd)line[i]=0;
           }

           tmp = strdup(line);
           returnString = getfield(tmp,15,"");
           free (tmp);
           if (returnString !="")
           {
              tmp = strdup(line);
              printf("  '%s': ",getfield(tmp,1,"0"));
              printf("  \"%s\" ,\n",returnString);
              free (tmp);
           }
        }
        printf("}\n");
        fclose(stream);
}

