#include <stdio.h> 
#include <netdb.h>
#include <unistd.h>
#include <netinet/in.h> 
#include <stdlib.h> 
#include <string.h> 
#include <sys/socket.h> 
#include <sys/types.h>
#include <arpa/inet.h>

union IxgbeLogEntry {
  long long data[8];
  struct {
    long long tsc;    
    long long ninstructions;
    long long ncycles;
    long long nref_cycles;
    long long nllc_miss;
    long long joules;
    
    int rx_desc;
    int rx_bytes;
    int tx_desc;
    int tx_bytes;
  } __attribute((packed)) Fields;
} __attribute((packed));

#define IXGBE_CACHE_LINE_SIZE 64
#define IXGBE_LOG_SIZE 1000000

struct IxgbeLog {
  uint64_t itr_joules_last_tsc;
  uint32_t itr_cnt;
  uint32_t msg_size;
  uint32_t repeat;
  uint32_t dvfs;
  uint32_t rapl;
  uint32_t itr;
  uint32_t iter;  
  uint64_t work_start;
  uint64_t work_end;

  float pk0j;
  float pk1j;
  float tput;
  float lat;
  
  union IxgbeLogEntry log[IXGBE_LOG_SIZE];
} __attribute__((packed, aligned(IXGBE_CACHE_LINE_SIZE)));

#define FNAMESIZE 256
//struct IxgbeLog ixgbe_logs;

int main(int argc, char **argv) {
  /* declare a file pointer */
  FILE    *infile;
  char    *buffer;
  long    numbytes;
  union IxgbeLogEntry *le;
  int i, num_entries;
  long long rdtsc_check = 0;
  char tput_filename[FNAMESIZE];
  char dmesg_filename[FNAMESIZE];
  int ret;
  FILE *fp;
  
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
  //printf("numbytes=%lu num_entries=%d\n", numbytes, num_entries);
  
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

  struct IxgbeLog *il = (struct IxgbeLog *)buffer;
  uint8_t* re = (uint8_t*)(buffer);
  uint64_t sum = 0;
  for(int i = 0; i < numbytes; i++) {
    sum += re[i];
  }
  

  memset(tput_filename, 0, FNAMESIZE);
  memset(dmesg_filename, 0, FNAMESIZE);
  //dmesg_devicelog.5_64_5000_12_0x1900_45
  ret = snprintf(tput_filename, FNAMESIZE, "ebbrt.np.out.%u_%u_%u_%u_0x%X_%u", il->iter, il->msg_size, il->repeat, il->itr, il->dvfs, il->rapl);
  if(ret < 0) {
    printf("Error: %d\n", __LINE__);
    exit(0);
  }
  fp = fopen(tput_filename, "w");
  if(fp == NULL) {
    printf("Error: %d\n", __LINE__);
      exit(0);
  }
  fprintf(fp, "%u %u %u 0x%X %u %u %.4f %.4f %.4f %.4f %llu %llu\n", il->iter, il->msg_size, il->repeat, il->dvfs, il->rapl, il->itr, il->pk0j, il->pk1j, il->tput, il->lat, il->work_start, il->work_end);    
  fclose(fp);     
  
  ret = snprintf(dmesg_filename, FNAMESIZE, "ebbrt.dmesg.%u_%u_%u_%u_0x%X_%u", il->iter, il->msg_size, il->repeat, il->itr, il->dvfs, il->rapl);
  if(ret < 0) {
    printf("Error: %d\n", __LINE__);
    exit(0);
  }
  
  fp = fopen(dmesg_filename, "w");
  if(fp == NULL) {
    printf("Error: %d\n", __LINE__);
    exit(0);
  }
  //printf("itr_cnt=%d sum=%llu\n", il->itr_cnt, sum);
  for (uint32_t i = 0; i < il->itr_cnt; i++) {
    union IxgbeLogEntry *ile = &il->log[i];
    //printf("%d %d %d %d %d %llu %llu %llu %llu %llu\n",
    fprintf(fp, "%d %d %d %d %d %llu %llu %llu %llu 0 0 0 %llu %llu\n",
	    i,
	    ile->Fields.rx_desc, ile->Fields.rx_bytes,
	    ile->Fields.tx_desc, ile->Fields.tx_bytes,
	    ile->Fields.ninstructions,
	    ile->Fields.ncycles,
	    ile->Fields.nref_cycles,
	    ile->Fields.nllc_miss,	    
	    ile->Fields.joules,
	    ile->Fields.tsc);
  }
  fclose(fp);     
    
  /* free the memory we used for the buffer */
  free(buffer);

}
