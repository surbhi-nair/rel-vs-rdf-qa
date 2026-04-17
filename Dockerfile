LABEL maintainer="Surbhi Nair <nairs@informatik.uni-freiburg.de>"

FROM pytorch/pytorch:1.12.1-cuda11.3-cudnn8-runtime

WORKDIR /masters_project
ENV PYTHONPATH "$PYTHONPATH:/masters_project"

COPY . .

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget aspell gcc g++ patch build-essential \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

CMD ["/usr/local/bin/entrypoint.sh"]

# BUILD
# docker build -f Dockerfile.gpu -t surbhi-nair-project:gpu .
#
# RUN (CPU)
# docker run -it -v /nfs/students/surbhi-nair:/extern/archive \
#   -v /local/data-hdd/nairs:/extern/data \
#   surbhi-nair-project:gpu
#
# RUN (GPU)
# docker run --gpus all -it -v /nfs/students/surbhi-nair:/extern/archive \
#   -v /local/data-hdd/nairs:/extern/data \
#   surbhi-nair-project:gpu