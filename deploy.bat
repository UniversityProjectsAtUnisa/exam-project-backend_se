ssh -t root@167.99.254.2 "su - arma -c 'cd /var/www/SE_Gruppo10_backend && cp .env /home/arma/ && git fetch --all && git pull --force && git checkout develop && mv /home/arma/.env . && pip3 install -r requirements.txt && pm2 reload all --update-env'"