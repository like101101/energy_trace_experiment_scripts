#include <stdio.h>
#include <stdlib.h>

union IxgbeLogEntry {
  long long data[11];
  struct {
    long long tsc;    
    long long ninstructions;
    long long ncycles;
    long long nref_cycles;
    long long nllc_miss;
    long long joules;
    long long c3;
    long long c6;
    long long c7;
        
    int rx_desc;
    int rx_bytes;
    int tx_desc;
    int tx_bytes;
  } __attribute((packed)) Fields;
} __attribute((packed));

int main(int argc, char **argv) {
  /* declare a file pointer */
  FILE    *infile;
  char    *buffer;
  long    numbytes;
  union IxgbeLogEntry *le;
  int i, num_entries;
  long long rdtsc_check = 0;
  
  if(argc != 2) {
    printf("usecase: ./parse_ebbrt_mcd FILENAME\n");
    return 0;
  }
  
  /* open an existing file for reading */
  infile = fopen(argv[1], "r");
 
  /* quit if the file does not exist */
  if(infile == NULL)
    return 1;
 
  /* Get the number of bytes */
  fseek(infile, 0L, SEEK_END);
  numbytes = ftell(infile);
  num_entries = numbytes/sizeof(union IxgbeLogEntry);
  printf("numbytes=%lu num_entries=%d\n", numbytes, num_entries);
  
  /* reset the file position indicator to 
     the beginning of the file */
  fseek(infile, 0L, SEEK_SET);	
 
  /* grab sufficient memory for the 
     buffer to hold the text */
  buffer = (char*)calloc(numbytes, sizeof(char));	
 
  /* memory error */
  if(buffer == NULL) {
    printf("buffer == NULL\n");
    return 1;
  }
 
  /* copy all the text into the buffer */
  fread(buffer, sizeof(char), numbytes, infile);
  fclose(infile);
  
  le = (union IxgbeLogEntry *)buffer;
  /*for(i=0;i<10;i++) {
    printf("%d %d %d %d %d %llu %llu %llu %llu %llu %llu %llu %llu %llu\n",
	   i,
	   le[i].Fields.rx_desc, le[i].Fields.rx_bytes,
	   le[i].Fields.tx_desc, le[i].Fields.tx_bytes,
	   le[i].Fields.ninstructions,
	   le[i].Fields.ncycles,
	   le[i].Fields.nref_cycles,	     
	   le[i].Fields.nllc_miss,
	   le[i].Fields.c3,
	   le[i].Fields.c6,
	   le[i].Fields.c7,
	   le[i].Fields.joules,
	   le[i].Fields.tsc);
  }
  printf("******\n");*/
  for(i=0;i<num_entries;i++) {
    printf("%d %d %d %d %d %llu %llu %llu %llu %llu %llu %llu %llu %llu\n",
	   i,
	   le[i].Fields.rx_desc, le[i].Fields.rx_bytes,
	   le[i].Fields.tx_desc, le[i].Fields.tx_bytes,
	   le[i].Fields.ninstructions,
	   le[i].Fields.ncycles,
	   le[i].Fields.nref_cycles,	     
	   le[i].Fields.nllc_miss,
	   le[i].Fields.c3,
	   le[i].Fields.c6,
	   le[i].Fields.c7,
	   le[i].Fields.joules,
	   le[i].Fields.tsc);
    
    if(rdtsc_check == 0) {
      rdtsc_check = le[i].Fields.tsc;
    } else if(le[i].Fields.tsc >= rdtsc_check) {
      le[i].Fields.tsc = rdtsc_check;
    } else {
      printf("Error %s failed rdtsc check\n", argv[1]);
      free(buffer);
      exit(0);
    }
  }   
  /* free the memory we used for the buffer */
  free(buffer);

}
