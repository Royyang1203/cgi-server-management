# CGI Server Management System

This is a Flask-based server management system. Below are instructions for running the project using Podman.

## Prerequisites

- Podman installed on your system
- Git (for cloning the repository)

## Setup and Running with Podman

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd cgi-server-manage
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file with your configurations
   ```

3. Build the container image:
   ```bash
   podman build -t cgi-server-manage .
   ```

4. Run the container:
   ```bash
   podman run -d \
     --name cgi-server \
     -p 5000:5000 \
     --env-file .env \
     cgi-server-manage
   ```

## Container Management Commands

### View container logs
```bash
podman logs cgi-server
```

### Stop the container
```bash
podman stop cgi-server
```

### Remove the container
```bash
podman rm cgi-server
```

### Restart the container
```bash
podman restart cgi-server
```

## Development

The application runs on port 5000 by default. You can access it at:
```
http://localhost:5000
```

## Environment Variables

Make sure to set up your environment variables in the `.env` file before running the container. You can use `.env.example` as a template.

## Troubleshooting

If you encounter any issues:

1. Check the container logs:
   ```bash
   podman logs cgi-server
   ```

2. Ensure all environment variables are properly set in your `.env` file

3. If the container fails to start, you can try running it in interactive mode:
   ```bash
   podman run -it --rm \
     --name cgi-server \
     -p 5000:5000 \
     --env-file .env \
     cgi-server-manage
   ``` 