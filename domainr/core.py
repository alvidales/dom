"""
Core functionality for Domainr.
"""

from argparse import ArgumentParser
import configparser
import pkg_resources
import requests
import simplejson as json
import sys
from termcolor import colored


class Domain(object):
    """Main class for interacting with the domains API."""

    def environment(self):
        """Parse any command line arguments."""
        parser = ArgumentParser()
        parser.add_argument('query', type=str, nargs='+',
                            help="Your domain name query.")
        parser.add_argument('-i', '--info', action='store_true',
                            help="Get information for a domain name.")
        parser.add_argument('--ascii', action='store_true',
                            help="Use ASCII characters for domain availability.")
        parser.add_argument('--available', action='store_true',
                            help="Only show domain names that are currently available.")
        parser.add_argument('--tld', action='store_true',
                            help="Only check for top-level domains.")
        args = parser.parse_args()
        return args

    def search(self, env):
        """Use domainr to get information about domain names."""
        
        query = " ".join(env.query)
        params = {'q': query}

        # Try and get the API key from the config file
        config = configparser.ConfigParser()
        configFilename = pkg_resources.resource_filename('domainr', 'domainr.ini')
        config.read(configFilename)
    
        if config['Default']['mashape-key']:
            params['mashape-key'] = config['Default']['mashape-key']
            url = "https://domainr.p.mashape.com"
        elif config['Default']['client_id']:
            params['client_id'] = config['Default']['client_id']
            url = "https://api.domainr.com"
        else:
            sys.exit("Error: No API key provided in config file at:\n"
                + "{0}\n".format(configFilename) 
                + "See the README for more info")

        if env.info:
            url += "/v1/info"
        else:
            url += "/v1/search"

        json_data = requests.get(url, params=params)
        # print(json_data.url)

        if not json_data.status_code == 200:
            return "Error: Status {0}; Response: {1}".format(json_data.status_code, json_data._content)
        data = self.parse(json_data.content, env)
        if not data:
            return "No results found\n"
        else:
            return data

    def parse(self, content, env):
        """Parse the relevant data from JSON."""
        data = json.loads(content)
        if not env.info:
            # Then we're dealing with a domain name search.
            output = []
            results = data['results']
            for domain in results:
                name = domain['domain']
                availability = domain['availability']
                if availability == 'available':
                    name = colored(name, 'blue', attrs=['bold'])
                    symbol = colored(u"\u2713", 'green')
                    if env.ascii:
                        symbol = colored('A', 'green')
                else:
                    symbol = colored(u"\u2717", 'red')
                    if env.ascii:
                        symbol = colored('X', 'red')
                    # The available flag should skip these.
                    if env.available:
                        continue
                string = "%s  %s" % (symbol, name)
                # Now, a few sanity checks before we add it to the output.
                if env.tld:
                    if self._tld_check(domain['domain']):
                        output.append(string)
                else:
                    output.append(string)
            return '\n'.join(output)
        # Then the user wants information on a domain name.
        return data

    def _tld_check(self, name):
        """Make sure we're dealing with a top-level domain."""
        if name.endswith(".com") or name.endswith(".net") or name.endswith(".org"):
            return True
        return False

    def main(self):
        args = self.environment()
        print(self.search(args))
