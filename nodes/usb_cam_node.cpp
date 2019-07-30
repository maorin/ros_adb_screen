#include <ros/ros.h>
#include <image_transport/image_transport.h>
#include <opencv2/highgui/highgui.hpp>
#include <cv_bridge/cv_bridge.h>
#include <sstream>
#include <iostream>
#include <std_srvs/Empty.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <errno.h>

namespace ros_adb_screen {


const int BANNER = 0;
const int BANNER_SIZE = 24;
const int HEAD =  1;
const int HEAD_SIZE  = 4;
const int DATA = 2;
static const char hex_table[16] = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F'};

void error(const char *msg) {
	perror(msg);
	exit(0);
}

class UsbCamNode
{
public:
  // private ROS node handle
  ros::NodeHandle node_;

  // shared image message
  sensor_msgs::Image img_;
  image_transport::Publisher image_pub_;



	int sockfd, portno, n;
	struct sockaddr_in serv_addr;
	struct hostent *server;

	char buffer[1024 * 1024];
	int state = BANNER;
	unsigned int data_size;
	std::string banner_data;
	std::string head_data;
	char img_data[1024 * 1024];
	int is_capturing = 1;

	std::string data;




  UsbCamNode() :
      node_("~")
  {
    // advertise the main image topic
    image_transport::ImageTransport it(node_);
    image_pub_ = it.advertise("image_raw", 1);


	portno = atoi("1313");
	sockfd = socket(AF_INET, SOCK_STREAM, 0);
	if (sockfd < 0)
		error("ERROR opening socket");
	server = gethostbyname("localhost");
	if (server == NULL) {
		fprintf(stderr, "ERROR, no such host\n");
		exit(0);
	}
	bzero((char *) &serv_addr, sizeof(serv_addr));
	serv_addr.sin_family = AF_INET;
	bcopy((char *) server->h_addr, (char *) &serv_addr.sin_addr.s_addr,
			server->h_length);
	serv_addr.sin_port = htons(portno);
	if (connect(sockfd, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0) {}

  }

  virtual ~UsbCamNode()
  {
	 close(sockfd);
  }



  bool take_and_send_image()
  {
    return true;
  }




  bool spin()
  {
    ros::Rate loop_rate(30);
    while (node_.ok())
    {
    		bzero(buffer, 1024 * 1024);
    		std::string output;
    		output.resize(1024*1024);
    		n = read(sockfd,  &output[0], 1024 * 1024-1);
    		//output[n] = 0;
    		if (n < 0) {
    			//if(errno == EINTR)  return -1;
        		if(errno == EAGAIN || errno == EWOULDBLOCK) {
        					continue;
        		}
    			error("ERROR reading from socket");
    			return -1;
    		}

    		data = data + output.substr(0, n);
    		/**
			printf("bufffffffffffff\n");
			for (int i = 0; i < 24; i++) {
				printf("%02X", (unsigned char) output[i]);
			}
			printf("\n");


			printf("xxxxxxxxxxxx\n");
			for (int i = 0; i < 24; i++) {
				printf("%02X", (unsigned char) data[i]);
			}
				printf("\n");
			**/

    		if ((state == BANNER) && (data.size() >= BANNER_SIZE)) {
				banner_data = data.substr(0, BANNER_SIZE);
				printf("bbbbbbbbbaaa\n");
       		    for (int i = 0; i < 24; ++i) {
       		        printf("%02X",(unsigned char) banner_data[i]);
       		    }
       		    printf("\n");

       		    //strcpy(data, &data[BANNER_SIZE]);
       		    data = data.substr(BANNER_SIZE, data.size()-BANNER_SIZE);
       		    //data.erase(0, BANNER_SIZE);
    			state=HEAD;
    		}

    		if ((state == HEAD) && (data.size() >= HEAD_SIZE)) {
    			char head_data[4];
				for (int i = 0; i < 4; ++i){
					head_data[i] = data[i];
				}
				//head_data = data.substr(0, HEAD_SIZE);
    			data = data.substr(HEAD_SIZE, data.size()-HEAD_SIZE);


				for (int i = 0; i < 4; ++i) {
					printf("%02X", (unsigned char)head_data[i]);
				}
    			//data_size =  head_data[0] | (head_data[1] << 8) | (head_data[2] << 16) | (head_data[3] << 24);
          		//data_size = head_data[0] + head_data[1]*256 + head_data[2]*256 * 256 + head_data[3]* 256 * 256 * 256;

				memcpy(&data_size, head_data, 4);


          		//data.erase(0, HEAD_SIZE);
    			state = DATA;
    			printf("data_size:%d\n", data_size);
    		}

    		if ((state == DATA) && (data.size() >= data_size)) {
    			std::string pub_data;
    			pub_data.resize(1024*1024);
    			pub_data = data.substr(0, data_size);
    			data = data.substr(data_size, data.size()-data_size);
    			//data.erase(0, data_size);

    			//cv::Mat image_data =  cv::Mat(data_size, 1, CV_8U, data);
    			std::vector<uchar> adata(pub_data.begin(), pub_data.end());

    			cv::Mat image = cv::imdecode(adata, CV_LOAD_IMAGE_COLOR);
    			sensor_msgs::ImagePtr msg = cv_bridge::CvImage(std_msgs::Header(), "bgr8", image).toImageMsg();
    			image_pub_.publish(msg);
    			cv::waitKey(1);
    			state = HEAD;
    		}






      ros::spinOnce();
      loop_rate.sleep();

    }
    return true;
  }






};

}

int main(int argc, char **argv)
{
  ros::init(argc, argv, "usb_cam");
  ros_adb_screen::UsbCamNode a;
  a.spin();
  return EXIT_SUCCESS;
}
