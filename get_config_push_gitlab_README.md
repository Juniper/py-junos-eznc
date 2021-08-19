# Use Case No. 1

### Overview
This python script was built by putting together small portions of code available at the "[Junos PyEZ Developer Guide](https://www.juniper.net/documentation/en_US/junos-pyez/information-products/pathway-pages/junos-pyez-developer-guide.html)" aiming to automaticatically feed a Git repository with Network configuration data (may the Network Engineers fail/forget to do so), keeping the teams distributed across different timezones informed and making it  easy to co-relate events and/or incidents to changes (to begin with), thus making troubleshooting smoother.

![Example No.1 Diagram](/images/ex-no1.png)

### Workflow
* The script is set to run from a cron job call at a predetermined schedule.
* A NETCONF session over SSH is established to all nodes in the `.yml` file sequentially.
* A [`get_config()`](https://www.juniper.net/documentation/us/en/software/junos/netconf/topics/ref/tag/netconf-get-config.html) Remote Procedure Call (RPC) is executed to request the complete configuration.
* On receiving the config it opens/creates a file (for each node) to write the data into, and name it after the entry on the `.yml` file for which it's performing the RPC to, and makes it a `.txt` on closing the file. 
* Upon completion the script runs [`git add --all`](http://git-scm.com/docs/git-add) to add them all to the repo, then [`git commit`](http://git-scm.com/docs/git-commit) and [`git push`](http://git-scm.com/docs/git-push).

Happy Labbing!

/me
