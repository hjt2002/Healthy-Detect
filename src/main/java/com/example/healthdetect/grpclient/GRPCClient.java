package com.example.healthdetect.grpclient;


import com.example.grpc.GreeterGrpc;
import com.example.grpc.HelloReply;
import com.example.grpc.HelloRequest;
import com.example.healthdetect.common.RespBeanEnum;
import com.example.healthdetect.exception.GlobalException;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.grpc.StatusRuntimeException;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;
public class GRPCClient {
    private static final Logger logger = Logger.getLogger(GRPCClient.class.getName());

    private final ManagedChannel channel;
    private final GreeterGrpc.GreeterBlockingStub blockingStub;

    /**
     * Construct client connecting to HelloWorld server at {@code host:port}.
     */
    public GRPCClient(String host, int port) {
        // 创建与服务器的通信通道
        try {
            channel = ManagedChannelBuilder.forAddress(host, port)
                    .usePlaintext()
                    .build();

            // 创建 Greeter 的阻塞存根
            blockingStub = GreeterGrpc.newBlockingStub(channel);
        } catch (Exception e) {
            throw new GlobalException(RespBeanEnum.GRPC_ERROR);
        }

    }

    public void shutdown() throws InterruptedException {
        channel.shutdown().awaitTermination(5, TimeUnit.SECONDS);
    }

    /**
     * Say hello to server.
     */
    public HelloReply greet(String name) {
        logger.info("Will try to greet server of" + name + " ...");
        HelloRequest request = HelloRequest.newBuilder().setName(name).build();
        HelloReply response = null;
        try {
            response = blockingStub.sayHello(request);

        } catch (StatusRuntimeException e) {
            logger.log(Level.WARNING, "RPC failed: {0}", e.getStatus());
            return response;
        }
//         输出信息
        logger.info("Greeting from server: " + response.getDate()
                                                        + " " + response.getType()
                                                        + " " + response.getBase64Url());
        return response;

    }

    /**
     * Greet server. If provided, the first element of {@code args} is the name to use in the
     * greeting.
     */
    public static void main(String[] args) throws Exception {
        // 定义访问的客户端
        GRPCClient client = new GRPCClient("localhost", 50001);
        try {
            String user = "hjt";
            if (args.length > 0) {
                user = args[0];
            }
            client.greet(user);

        } finally {
            client.shutdown();
        }
    }
}