#include <stdio.h> 
#include <netdb.h>
#include <unistd.h>
#include <netinet/in.h> 
#include <stdlib.h> 
#include <string.h> 
#include <sys/socket.h> 
#include <sys/types.h>
#include <arpa/inet.h>

#define PORT 8888
#define SA struct sockaddr 
#define FNAMESIZE 256

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

struct IxgbeLog ixgbe_logs;

char *buff;
uint64_t buff_size = sizeof(ixgbe_logs); // 51200064
  
// Function designed for chat between client and server. 
void func(int sockfd) 
{
  uint64_t n;
  uint64_t bytesLeft;
  uint64_t bytesRead;
  uint64_t total_read;
  char tput_filename[FNAMESIZE];
  char dmesg_filename[FNAMESIZE];
  int ret;
  FILE *fp;
  
  // infinite loop for chat 
  for (;;) {
    bytesLeft = buff_size;
    bytesRead = 0;
    total_read = 0;
    char *q = buff;    
    bzero(q, buff_size);   

    printf("bytesLeft=%d\n", bytesLeft);
    while(bytesLeft > 0 &&
	  (bytesRead = read(sockfd, q, bytesLeft)) > 0) {
      bytesLeft -= bytesRead;
      q += bytesRead;
      total_read += bytesRead;
      printf("bytesLeft=%d bytesRead=%d\n", bytesLeft, bytesRead);
    }

    if(bytesLeft > 0 && bytesRead == 0) {
      printf("bytesLeft > 0 && bytesRead == 0\n");
    } else if(bytesRead == -1) {
      printf("bytesRead == -1\n");
      exit(-1);
    }
    
    printf("Server received %lu bytes / %lu bytes\n", total_read, buff_size);
    
    //printf("From client: %s\n", buff);
    uint8_t* re = (uint8_t*)buff;
    uint64_t sum = 0;
    for(uint64_t i = 0; i < buff_size; i++) {
      sum += re[i];
    }
    
    struct IxgbeLog *il = (struct IxgbeLog *)buff;
    printf("itr_cnt=%d sum=%lu\n", il->itr_cnt, sum);

    /*memset(tput_filename, 0, FNAMESIZE);
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
    
    //printf("MSG=%u REPEAT=%u DVFS=0x%X RAPL=%u ITR=%u ITER=%u PK0=%u PK1=%u TPUT=%.4f LAT=%.4f\n",
    //il->msg_size, il->repeat, il->dvfs, il->rapl, il->itr, il->iter, il->pk0, il->pk1,
    //	   il->tput, il->lat);
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
    for (uint32_t i = 0; i < il->itr_cnt; i++) {
      union IxgbeLogEntry *ile = &il->log[i];
      //printf("%d %d %d %d %d %llu %llu %llu %llu %llu\n",
      fprintf(fp, "%d %d %d %d %d %llu %llu %llu %llu %llu %llu %llu %llu %llu\n",
	      i,
	      ile->Fields.rx_desc, ile->Fields.rx_bytes,
	      ile->Fields.tx_desc, ile->Fields.tx_bytes,
	      ile->Fields.ninstructions,
	      ile->Fields.ncycles,
	      ile->Fields.nref_cycles,
	      ile->Fields.nllc_miss,
	      ile->Fields.c3,
	      ile->Fields.c6,
	      ile->Fields.c7,
	      ile->Fields.joules,
	      ile->Fields.tsc);
    }*/
    //fclose(fp);     
    printf("\n******************************\n\n");
  }
} 

// Driver function 
int main() 
{ 
    int sockfd, connfd, len; 
    struct sockaddr_in servaddr, cli; 
    int optval; /* flag value for setsockopt */

    // socket create and verification 
    sockfd = socket(AF_INET, SOCK_STREAM, 0); 
    if (sockfd == -1) { 
        printf("socket creation failed...\n"); 
        exit(0); 
    } 
    else {
        printf("Socket successfully created..\n");
    }
   /* setsockopt: Handy debugging trick that lets 
    * us rerun the server immediately after we kill it; 
    * otherwise we have to wait about 20 secs. 
    * Eliminates "ERROR on binding: Address already in use" error. 
    */
    optval = 1;
    setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, 
	       (const void *)&optval , sizeof(int));

  
    bzero(&servaddr, sizeof(servaddr)); 
  
    // assign IP, PORT 
    servaddr.sin_family = AF_INET; 
    servaddr.sin_addr.s_addr = htonl(INADDR_ANY); 
    servaddr.sin_port = htons(PORT); 
  
    // Binding newly created socket to given IP and verification 
    if ((bind(sockfd, (SA*)&servaddr, sizeof(servaddr))) != 0) { 
        printf("socket bind failed...\n"); 
        exit(0); 
    } 
    else
        printf("Socket successfully binded..\n"); 

    buff = (char *)malloc(buff_size * sizeof(char));
    printf("buff_size=%d\n", buff_size);
    
    // Now server is ready to listen and verification 
    if ((listen(sockfd, 5)) != 0) { 
        printf("Listen failed...\n"); 
        exit(0); 
    } 
    else
        printf("Server listening..\n"); 
    len = sizeof(cli); 
  
    // Accept the data packet from client and verification 
    connfd = accept(sockfd, (SA*)&cli, &len); 
    if (connfd < 0) { 
        printf("server acccept failed...\n"); 
        exit(0); 
    } 
    else {
        printf("server acccept the client...\n"); 
    }    
    
    // Function for chatting between client and server 
    func(connfd); 
  
    // After chatting close the socket 
    close(sockfd); 
} 
