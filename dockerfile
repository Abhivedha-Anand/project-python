CONTAINERS=$(docker ps -aq)
if [ ! -z "$CONTAINERS" ]; then
  docker rm -f $CONTAINERS
fi
docker build -f /home/ec2-user/jenkins/workspace/Devops_Production_Pipeline/Dockerfile -t hotelreservation /home/ec2-user/jenkins/workspace/Devops_Production_Pipeline/
 
docker run -it -p 5000:5000 -d  hotelreservation
