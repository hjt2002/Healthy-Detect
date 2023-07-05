package com.example.healthdetect.grpcserver;
//import com
import com.example.grpc.GreeterGrpc;
import com.example.grpc.HelloReply;
import com.example.grpc.HelloRequest;
import io.grpc.Server;
import io.grpc.ServerBuilder;
import io.grpc.stub.StreamObserver;

import java.io.IOException;
import java.util.logging.Logger;

public class GRPCServer {
    private static final Logger logger = Logger.getLogger(GRPCServer.class.getName());

    /* The port on which the server should run */
    private int port = 50051;
    private Server server;

    private void start() throws IOException {
        //// 创建服务器，并指定监听的端口号
        server = ServerBuilder.forPort(port)
                .addService( new GreeterImpl())
                .build()
                .start();
        logger.info("Server started, listening on " + port);

        // JVM 关闭时执行的钩子方法，用于优雅关闭服务器
        Runtime.getRuntime().addShutdownHook(new Thread() {
            @Override
            public void run() {
                // Use stderr here since the logger may have been reset by its JVM shutdown hook.
                System.err.println("*** shutting down gRPC server since JVM is shutting down");
                GRPCServer.this.stop();
                System.err.println("*** server shut down");
            }
        });
    }

    private void stop() {
        if (server != null) {
            server.shutdown();
        }
    }

    /**
     * Await termination on the main thread since the grpc library uses daemon threads.
     */
    private void blockUntilShutdown() throws InterruptedException {
        if (server != null) {
            server.awaitTermination();
        }
    }

    /**
     * Main launches the server from the command line.
     */
    public static void main(String[] args) throws IOException, InterruptedException {
        final GRPCServer server = new GRPCServer();
        server.start();
        server.blockUntilShutdown();
    }

    static class GreeterImpl extends GreeterGrpc.GreeterImplBase {
        /** 原子Integer */
        //    public AtomicInteger count = new AtomicInteger(0);

        @Override
        public void sayHello(HelloRequest req, StreamObserver<HelloReply> responseObserver) {
            logger.info("from client: " + req.getName());
//            System.out.println("call sayHello");
            HelloReply reply = HelloReply.newBuilder().setMessage("Hello " + req.getName()).build();
            responseObserver.onNext(reply);
            responseObserver.onCompleted();
//            System.out.println(count.incrementAndGet() + Thread.currentThread().getName());
        }
    }
}