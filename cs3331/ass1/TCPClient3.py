TCPServer3.py                                                                                       0000660 0103225 0103225 00000042605 14227533352 012213  0                                                                                                    ustar   z5115499                        z5115499                                                                                                                                                                                                               """
    Sample code for Multi-Threaded Server
    Python 3
    Usage: python3 TCPserver3.py 12000
    coding: utf-8
    
    Author: Alex Piotrowski
"""
from socket import *
from threading import Thread
import sys, select
import time
from datetime import datetime
import os.path
from os import path


# acquire server host and port from command line parameter
if len(sys.argv) != 2:
    print("\n===== Error usage, python3 TCPServer3.py SERVER_PORT ======\n")
    exit(0)
serverHost = "127.0.0.1"
serverPort = int(sys.argv[1])
serverAddress = (serverHost, serverPort)

# define socket for the server side and bind address
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(serverAddress)

logged_in_users = []

"""
    Define multi-thread class for client
    This class would be used to define the instance for each connection from each client
    For example, client-1 makes a connection request to the server, the server will call
    class (ClientThread) to define a thread for client-1, and when client-2 make a connection
    request to the server, the server will call class (ClientThread) again and create a thread
    for client-2. Each client will be runing in a separate therad, which is the multi-threading
"""
class ClientThread(Thread):
    def __init__(self, clientAddress, clientSocket):
        Thread.__init__(self)
        self.clientAddress = clientAddress
        self.clientSocket = clientSocket
        self.clientAlive = False
        self.clientUsername = ""
        
        print("===== New connection created for: ", clientAddress)
        self.clientAlive = True
        
    def run(self):
        message = ''
        
        while self.clientAlive:
            # use recv() to receive message from the client
            data = self.clientSocket.recv(1024)
            message = data.decode()
            
            # if the message from client is empty, the client would be off-line then set the client as offline (alive=Flase)
            if message == '':
                self.clientAlive = False
                print("===== the user disconnected - ", clientAddress)
                break
            
            # handle message from the client
            if message.startswith("login"):
                print("[recv] New login request")
                data = message.split()
                username = data[1]
    
                if username in logged_in_users:
                    self.clientSocket.send("User has already logged in".encode())
                elif (self.does_user_exist_in_credentials_txt(username) == False):
                    print("User does not exist - creating new user")
                    self.clientSocket.send("user does not exist - creating new user account".encode())
                    password_data = self.clientSocket.recv(1024)
                    password = password_data.decode()

                    fp = open("credentials.txt", 'a')
                    fp.write(username + " " + password + "\n")
                    fp.close()

                    self.clientSocket.send("user created".encode())
                else: 
                    print("User exists - requesting password")
                    self.clientSocket.send("user confirmed - please provide password".encode())
                    password_data = self.clientSocket.recv(1024)
                    password = password_data.decode()

                    if (self.process_authenication(username, password) == False):
                        self.clientSocket.send("incorrect password".encode())
                    else:
                        print("Authenication successful")
                        logged_in_users.append(username)
                        print(logged_in_users)
                        self.clientSocket.send("user authenication successful".encode())
                
            elif message == 'download':
                print("[recv] Download request")
                message = 'download filename'
                print("[send] " + message)
                self.clientSocket.send(message.encode())
            elif message.startswith("MSG"):
                print("[recv] Post message request")
                data = message.split()
                if len(data) < 4:
                    # incorrect number of arguments. - return error
                    self.clientSocket.send("Error with posting message - Incorrect number of arguments".encode())
                elif self.does_thread_exist(data[1]) == False: 
                    self.clientSocket.send("Error with posting message - Thread does not exist".encode())
                else: 
                    line_number = self.get_number_of_lines_from_file(data[1])
                    fp = open(data[1], 'a')
                    fp.write(str(line_number) + " " + str(data[-1]) + ": " + " ".join(str(x) for x in data[2:-1]) + "\n")
                    fp.close()

                    self.clientSocket.send("Message posted successfully!".encode())
            elif message.startswith("CRT"):
                print("[recv] create new thread request")
                data = message.split()
                if len(data) != 3:
                    self.clientSocket.send("Error with creating thread - Incorrect number of arguments".encode())
                else:
                    print(data[0])
                    print(data[1])
                    username = data[2]
                    does_thread_exist = path.exists(data[1])
                    if does_thread_exist == True:
                        self.clientSocket.send("Error with creating thread - Threadtitle already exists".encode())
                    else:
                        fp = open(data[1], 'w')
                        if username == "":
                            fp.close()
                            os.remove(data[1])
                            self.clientSocket.send("Error with creating thread - User is not logged in.".encode())
                        else: 
                            fp.write(username)
                            fp.write("\n")
                            fp.close()
                            self.clientSocket.send("Thread created".encode())
            elif message.startswith("DLT"):
                print("[recv] delete message in thread request")
                data = message.split()
                if len(data) != 4:
                    self.clientSocket.send("Error deleting message from thread - Incorrect number of arguments".encode())
                else: 
                    thread = data[1]
                    message_number = data[2]
                    user = data[3]

                    # check if the thread exists
                    if (self.does_thread_exist(thread) == False):
                        self.clientSocket.send("Error deleting message from thread - Thread does not exist".encode())
                    
                    # check if the message number exists in the thread
                    elif (self.check_message_number_is_valid_in_thread(thread, message_number) == False):
                        self.clientSocket.send("Error deleting message from thread - Message number does not exist".encode())

                    # check if the user made this message number
                    elif (self.check_message_number_belongs_to_user(thread, message_number, user) == False):
                        self.clientSocket.send("Error deleting message from thread - You are not the owner of the message".encode())
                    else: 
                        self.delete_message_number_from_thread(thread, message_number)
                        self.clientSocket.send("Successfully deleted message from thread".encode())
            elif message.startswith("EDT"):
                print("[recv] edit message in thread request")
                data = message.split()
                if len(data) < 5:
                    self.clientSocket.send("Error with editing message from thread - Incorrect number of arguments".encode())
                else: 
                    thread = data[1]
                    message_number = data[2]
                    message = data[3:-1]
                    user = data[-1]

                    if (self.does_thread_exist(thread) == False):
                        self.clientSocket.send("Error with editing message from thread - Thread does not exist".encode())
                    elif (self.check_message_number_is_valid_in_thread(thread, message_number) == False):
                        self.clientSocket.send("Error with editing message from thread - Message number does not exist".encode())
                    elif (self.check_message_number_belongs_to_user(thread, message_number, user) == False):
                        self.clientSocket.send("Error with editing message from thread - You are not the owner of the message".encode())
                    else:
                        self.edit_message_number_from_thread(thread, message_number, message) 
                        self.clientSocket.send("Successfully edited message from thread".encode())
            elif message.startswith("LST"):
                print("[recv] List threads request")
                list_of_threads = []
                for root, dirs, files in os.walk("."):
                    for file in files:
                        if (str(file).endswith(".py") == False and str(file).endswith(".txt") == False):
                            list_of_threads.append(str(file))
                self.clientSocket.send(" ".join(list_of_threads).encode())
            elif message.startswith("RDT"):
                print("[recv] read thread request")
                data = message.split()
                if len(data) != 2:
                    self.clientSocket.send("Error with reading thread - Incorrect number of arguments".encode())    
                else: 
                    thread = data[1]
                    if (self.does_thread_exist(thread) == False):
                        self.clientSocket.send("Error with editing message from thread - Thread does not exist".encode())
                    else: 
                        fp = open(thread, 'r')
                        lines = fp.readlines()
                        fp.close()
                        lines[0] = "RDT"
                        self.clientSocket.send("".join(lines).encode())
            elif message.startswith("RMV"):
                print("[recv] remove thread request")
                data = message.split()
                if len(data) != 3:
                    self.clientSocket.send("Error with removing thread - Incorrect number of arguments".encode())
                else: 
                    thread = data[1]
                    user = data[2]
                    if (self.does_thread_exist(thread) == False):
                        self.clientSocket.send("Error with removing thread - Thread does not exist".encode())
                    elif (self.check_if_thread_belongs_to_user(thread, user) == False):
                        self.clientSocket.send("Error with removing thread - Thread does belong to user".encode())
                    else:
                        self.remove_thread(thread)
                        self.clientSocket.send("Thread removed successfully".encode())
            elif message.startswith("XIT"):
                data = message.split()
                user = data[1]
                logged_in_users.remove(user)
            else:
                print("[recv] " + message)
                print("[send] Cannot understand this message")
                message = 'Cannot understand this message'
                self.clientSocket.send(message.encode())
    
    """
        You can create more customized APIs here, e.g., logic for processing user authentication
        Each api can be used to handle one specific function, for example:
        def process_login(self):
            message = 'user credentials request'
            self.clientSocket.send(message.encode())
    """
    def remove_thread(self, thread):
        os.remove(thread)

    def check_if_thread_belongs_to_user(self, thread, user):
        fp = open(thread, 'r')
        line = fp.readline()
        fp.close()

        if (line.startswith(user) == True):
            return True
        else:
            return False

    def edit_message_number_from_thread(self, thread, message_number, message):
        fp = open(thread, 'r')
        lines = fp.readlines()
        fp.close()

        fp = open(thread, 'w')
        for number, line in enumerate(lines):
            if number != int(message_number):
                fp.write(line)
            else: 
                line_data = line.split()
                newline = " ".join(line_data[0:2]) + " " + " ".join(message)
                print(newline)
                fp.write(newline + "\n")
        fp.close()

    def delete_message_number_from_thread(self, thread, message_number):
        fp = open(thread, 'r')
        lines = fp.readlines()
        fp.close()

        fp = open(thread, 'w')
        for number, line in enumerate(lines):
            if number > int(message_number):
                line_data = line.split()
                line_data[0] = str(int(line_data[0]) - 1)
                newline = " ".join(line_data)
                print(newline)
                fp.write(newline + "\n")
            elif number != int(message_number):
                fp.write(line)
        fp.close()


    def check_message_number_belongs_to_user(self, thread, message_number, user):
        FILE = open(thread, 'r')
        lines = FILE.readlines()
        for line in lines:
            line_data = line.split()
            if (len(line_data) != 1): 
                # the line number is the first element in the array
                if str(message_number) == line_data[0]:
                    FILE.close()
                    if str(user) + ":" == line_data[1]:
                        return True
                    else:
                        return False
        FILE.close()
        return False

    def check_message_number_is_valid_in_thread(self, thread, message_number):
        FILE = open(thread, 'r')
        lines = FILE.readlines()
        for line in lines:
            line_data = line.split()
            if (len(line_data) != 1): 
                # the line number is the first element in the array
                if str(message_number) == line_data[0]:
                    FILE.close()
                    return True
        FILE.close()
        return False


    def get_number_of_lines_from_file(self, file_name):
        with open(file_name, 'r') as fp:
            number_of_lines = len(fp.readlines())
            return number_of_lines

    def does_thread_exist(self, thread_name):
        return path.exists(thread_name)



    def process_login(self, username):
        message = 'user credentials request'
        print('[send] ' + message)
        self.clientSocket.send(message.encode())

        result = ""

        print("[recv] recieved username: " + username)

        does_user_exist = self.does_user_exist_in_credentials_txt(username)

        print(does_user_exist)

        if does_user_exist == True:
            # we move onto the next phase - password authenication

            print('[send] ' + "Confirmation - User Exist")
            self.clientSocket.send("user exists".encode())

            # we request the client to send us a password
            password_data = self.clientSocket.recv(1024)
            password = password_data.decode()
            print(password)
            password_auth_result = self.process_authenication(username, password)
            print(password_auth_result)

            if password_auth_result == True:
                result = "Login Successful"
            else: 
                result = "Error - Incorrect password"

        else:
            self.clientSocket.send("Error - User does not exist".encode())

            # awaiting a new password from the client
            password_data = self.clientSocket.recv(1024)
            password = password_data.decode()
            print("new password is: " + password)

            self.add_user_to_credentials_txt(username, password)

            result = "User created"



        
        return result
        

    def process_authenication(self, username, password):
        FILE = open('credentials.txt', 'r')
        status = False
        for one_profile in FILE:
            data = one_profile.split()
            if data[0] == username and data[1] == password:
                status = True
        return status 
        

    def does_user_exist_in_credentials_txt(self, username):
        FILE = open('credentials.txt', 'r')
        status = False
        for one_profile in FILE:
            data = one_profile.split()
            if data[0] == username:
                status = True
        return status

    def add_user_to_credentials_txt(self, username, password):
        FILE = open('credentials.txt', 'a')
        FILE.write(username + ' ' + password + '\n')




print("\n===== Server is running =====")
print("===== Waiting for connection request from clients...=====")


while True:
    serverSocket.listen()
    clientSockt, clientAddress = serverSocket.accept()
    clientThread = ClientThread(clientAddress, clientSockt)
    clientThread.start()
                                                                                                                           cs3331-report.pdf                                                                                   0000644 0103225 0103225 00000223132 14227540052 012655  0                                                                                                    ustar   z5115499                        z5115499                                                                                                                                                                                                               %PDF-1.5
%äüöß
2 0 obj
<</Length 3 0 R/Filter/FlateDecode>>
stream
x��XI��F��W����[����eHnr9e;M��%?��"Y֛��i���������{�ڙ��ƦΏ���wi�>��q����oY��o�淓}�bt��������:��۟�\L�b�t���:Lg�Ͽ`�If�����x{�~}�鴼�>���gw�{���#� X98y�#*���� D��Z�л'�` ����Jtϣ�ɧ\Y�\�ݦs�o�<���,&3�2y����H}|6L�b��gD��$�nr!5>���.������W��Z�W݋���\��}h�1���wkZBy�,��h�w�腾�\c�[R�Ǐ�¯թd� UG�{��f%ԃq���Y�B���W4�1>=��r�s�h�)�K��K뭍[�mC;b�5��-�_�;Y��Jt~�,ty��A"Z��%�I7�<�ލ�O�@�a��@q�l'��%W_x2�؏/aS�f�.�J0^��0�(�a��ځ�-�;��1���)�w���6��"F!���.l��\��qZP�*!p�C�LR(�MD7JNq	�wS WҤ�S-��%����N�l�fq�]�q~3%��<C)�B�3T�@dU�H�q?�WL�W��O~I7��	�d����O���Sި-i�="�&��?y���[��[���ֲV�E��e-�-�������!�:��+��+����PײÆ�O��+�
#΍B�^6ݬ�^�1��N{�wN���|�A[�8k��:��O::���H�H-����5��,�6v�r��LSD��4�ղ*�UFe.j�xU���;9�.�`y���� Ek;��[oֆe�Km��Jۼ^
f��8!&�E��v4���ݑ�V�:X��(��TW�v��Ll�w�i.�6W*�����c�.Fu� ^�YѠ�l]��ţ�����Af�U���1Oߢ-O�y������	�i�h, ]��<�m`�b�������v�Ȫ6�ׄR٪ج�Ė�t�,H(���H���
C�'���@���q�NK �c�|�,�󭰧�O�i�S�ǽ_J;7jSS��n�EL�%�^΅i�����ט~�7�F��H����If�Z:[��}�<W��F�*����%�Ba�"��uR^K���GG��*ʛ����Z�q����׍������Eq)�b!93Ŗz^7���Mm�����}-�#΢��1wU�Y��"+� �T �������|G���w_"�e���k&�~;gn
.�ā�6��7�]D����'���}э�o_N�~�2t�:�o��{
endstream
endobj

3 0 obj
1295
endobj

4 0 obj
<</Type/XObject/Subtype/Image/Width 879/Height 615/BitsPerComponent 8/Length 5 0 R
/Filter/FlateDecode/ColorSpace/DeviceRGB
/SMask 6 0 R
>>
stream
x���	T���Ͻ��s����{�I'�NR,
�
�����;�.�*(n����j��� ��v#�C&{�[2��t:��$�d��$��&7��������=ųTճ ؾ_�w8�T���_U=<�yj[���?��O���������B�P(
��H��$��������
�B�P(�cW~���I��{���n���:� ��ڟB�P(
��Ė_��o�/%%>L�p����=L�p��?m^��i�"y�p������_�p�O�P(
�B����z9U��W��p��n������?h�����u�Ao6�B�P(
e(ϳ%����i�_�����)���,�R�R4?���z�����?��T��S(
�B�P�Z)��ð����ۿ��Կz�~�����������q���ww���a������R(
�B�PB[~��_��'�����W��s�R���$��x�:��[�J���ɟ=��+�U���J���}f)
�B�P�"��wޖ�0�V���oy-o��(��7����7//��O�c�/w�|�+L~���A_�
��V��~������1�-�P(�Er�w����c��d aR���ʓF�4�K���sǫ0���o���P(ON����,_b���_������U�/~���_�L^���-��P'��-��g?���?P����U#��~���x)?���R����W}�#�K�Pe1'ɁΓ^s�u�4����_�d��D�ɏS��§P(ON��{�HJ|�u�����KW.I�߼����o�7_��7�z�J�ҡ�;����ە�._~����?����f�����}���↪���,�U���P(ONy睷U<3�����1�����{��[o���C:N��rp���~�u���g�%g�/
���aRJK�Ͼp�\Cc����~���o~�����WU����\~�	�����?��/���;��OK��կ���Fϟ�>�
��)����o���3&�C^~�{C+Lʗ�o���C:�q"������a���&�>�0y��P(�����k�7^Ee�&��Ϝ+�A?��G��׿��t7�4Jwk[�t���E�,��������V�U/����H��/T�THGC�=��S(ʣ,��/�d{��DǷ�R�I�%E:䥿y�~�����-I��a��R~0'���a�>�����)ʓP~��J�{�����P���?��?H,�����Wn�*���~���[�VS[��|���ߔ�7�|��z��������񍯪q�_J���}K:�7�&)ʠä_��oq��(�� �O����*y��<�?��@�� �5���aѠ/|
��/�+*�%��(�v�z�
��_�<s�����/Q�����-ҳ���܅�R�g?����}�/E�tu�&)�P.���_G���rk�?��|8y�G�
^�����;�Y/�����H����A_�
�I(�w��[~�����W�����x
�ByK�7-�c�͇�=�1�a�0����Ơ����<�?���a�{?�DJ
�B�P(J_���ޕ�h��6���H�Ao0�B�P(
�B�P(
�B�P(
�B�P(
�B�P(���              �G�L��'�ʄ��ݦ!��Z�s�bBIII���x  T�Ծ�� �����c&i�Ok{��nm{�6u�{�o�3�TN�0	  `6O_\�Q��?<R����y&�3�S?p�s���0;N{�v�-�BчZ��ڶ[Z��j�F�  ��m�z@:�e���w���
�`���X;��V�#mi�3V�gn%�I����n��\}�+�qWʘ���0	  a����\4o�v��z��y�u����ڊ������;Z�]=*��TF�1�Kq����k���Yzp�7�����ƹ��3m��-5=S�J�Nڠ�$jk/hG���P���SK?�E�p����K�gF���di�i�Uh�'���������[UU���V__�����chll����[ZZ������	�  `�K��I�'h���w,�s�c&%�e��g��is����+�I�iٮ:ˏ�/���d6c��_�� �ٶ!2ڕ`�J�W�I,:��<��;�s&���+**$^�vm��������t����/��_|1''Gj޹s�0	  ��Ň��t�-�{�5�{�}�:����Ak��]�3�]�"����u�1N���B����q�K���.�v��Q���S�k����&�7^��'��/Zr�5���R�q�ٶ�7�*�HF����ڠ_�c��h;	ɥj�,
m`aRң��={�}����Ν�ZJ�W��cǎ���n�"L �!��:=#m�ֻ��ֻ?�"��ձ�y���%���F)ᔈ��U6E�C�������p-�K�>�&�T�T,Nh�m���gwY-
�IH�i�<�Umy�5�jln$7>x��޽{���^+Kt�8�����M��  `(���	�w��_�K�݅��_5_a2:���aU����?O?���.���5==�)��A�'���_���N¤�6���w ��7�ݡSWx����Y&���7rU�8���Z��K2<w
����9�>)))�I  0�M^�=����;L��l�V��4��q�$ɼ7�Y��g��a�afor]gd����֓0HЕ�~з�2���3c�I�yy'�����mll4��4ia  e���f����-:�=L�Lp��^��s+�c�O(��o���gR�']����I�m��N[��Wy�^��$ܜ|W?�r{�^3�u��fj�����}U`�$  x�S}E���U���}N��v���r��Y��p�M���n���Mѯ�Vƥ��q��3�M��L�M��佡�/H^��f�ɛ{O���w������*O�]En1�1��Su5��[[�{M_�s&��BQQ�L ��ȈXי�kM{˦���'-t��n��~T��QV�5Nݪ7��7��=ƌ�+�G��nK��o�S̼�w�Є��u/�Lk�ޝ~�o�j�9LN^���V�o)���S�j{���-��$�ʨ�q�m����$Ҳ�����/R��n�)StN]͝����JI�����{�ʕ����>B�������F�CT   �5#ݕ��7���n]��4�����6�����k�~�\�']/�_&�t���\*9s�r�[݌(,L��N���iz�4n�&t�~�7ni�uu�gq;�m1	���n�����3y�С��J�}&oܸ!C/_�,C�fmmm`aR�Q�p   [j���K��m|�_��iڮW�=A�8v�ߡ1�Kz�}���jm��¸�>ƣ��&�T���Cz�T�-di�&,�v�k'�犻�'�X�AH�\yJߋx�M�=�i{���|�qzk�[\iS�Jΰo������������_�p��3��Ι3gfϞM�  ��4W�>Z�ٚb�j%n�~w �s�ɢ�ݴ   a�J����/c�n�"�   C��x�H�/�ǩ?�"�8�~�!bo���                      X�L��L�?�m����$%%��l   7�/.��D�(��I�]��4h9���*�Sh�	�2������򦦦�������;w�1"�����dPgg����ɓ�[���QXXڙ��X4 �'��=}qqGM_��H-~�^$�h�L����FU��1��q�s7�co�o,�P�{]�vK���y�ar���]]]��.\�P\\|��i@YYYDDD�*����YWWw��}'9m���Rm���4�^=� �ɱ���j�{�]-<½��C&'/�|S�#mi��mI�n%J���AB�z��[c1����dlllLL��2,,���Hڐ���
"55511Q:N�>m�Ӣ�����$څb���X4 �'DX�v�m=z�ۭ����1~�{�09|�����_��w�̻z>T$橌*c����m��ñ���*o�|r⺋zϴ}�fa�ZW�f��axA�6i��\�6z�_KBO{��jkk���?�|JJ�1T�����[ZZ�������֓߶m[ee�LB�OYYَ;,ƶt�Ri���������u�V��h�"���͛7_�|������C������Ǜ�e;�ΗC`�  !�4Ǖ�FO�}U�X��^�"LF�в[�w	��H���w�s��(=%d��lW������V�2��F����YXtP�|�zw��LFGGWTTH�v횄�ÇWWW_�tI�x���/��_|1''Gj�c�~�I�I�}����YYY2�+W�ܻw���$�H����Dۜ&���ݻ22������]2�'O��y,**joo�j2��g��r��   �֓ر���������=���+N��)�wi�Hw�,�~ߓ��S.����w���`��ˮ=�b�xm�m���Z���I��W͂W5~i�L7�0)�Nbɞ={�>?�Ν뚅իe�c��ˈ��[�n�&�'!$2�hͱG�5KNN���;u�Tmm���ƍ��B[A��i+V��
6l0���6u�Ts�ŋK�����d9�H  B���1l{��=o��]��կ�E��{]￧�����(e�&W���s�U6E�C���O�h�h{N��}�=L�1aRbE�8�x�y��gHc�衯j��Q~,�-<��Bqq�d����oڴɯ0i;	���r��M��_���׹s碢�B^A��i�B�.7H��������(�)((p>�N�CH	  �1\����;���һqy�j��dt���^��4����y��o�uQ_�����QLY��<��ڙ)a22Z�{Y�+�JjM�����2���S�����7�#���C�ǏW��Wu󾲔��¤�$Daa�Թz��֭[gϞ-y�W͘���K����]�~}�H���
�9-55�m/�yPIIIGGG�����Ϧ��p# @HH$��yO�&�L�
�+��E�]w�6I�yo����ϸ)�0i�[�y�hߨ$��ޤ�V5�Rf\w�f̘!�#/��l�^�������>�&M�+L�NB�1";;��ݻ*��׭[gQ�ܹ���S�:�I8lkk=���K�f͒y�޽]�vIX]�`AZZ���^p>�ΗC`�  �"y�kH��ѯڢ����W��U�n@�2<���r���>d�L}N�⤫b�+L&��֜��FF�7W_�_�z��M�{][Io�����Pn���.uR��{�܄jϤ�$��l�"!������iUyy�@T��i2/�0�R3uEϔ)S�>���na�`;��k$  u�⡯h�7���r����;~?�˕gy\�p�M���#���G��q��c���L���9��N�����J�/�3I?^����ծԂ��.�F���u?Ɛ�3�k��U?���			R���r *X䴣G�JN�4i�砒����fs�%K��
���lZT��   $Fĺnڳִ�l�j/�q�BW��V��G�XeU�kPV���U?n.3n�����W�Яݖ
��֧�y����i	3���^�VOLH?׷�R5�a�L���p.>��M�4Iݻ2����u�uVV��$%������+W�RGDD���p5��I�8�ne���Rٲe��U��5GEE�={�ܪ�+���i�������¡�3i�K&��Q�v6m+�H  3�]��|��Ѯ[�����~Ѵq��Qԕԑ�ھ6���U�\q��r�A�e�L�^Jɥ�3�.׻�͈�´���x)o���'I�f�֌{W����v�C�UVV��3y��z��e*5�}u��Ϥ�$$w������8%�uuu���W"���H�[�n�?^�������HA���W�z�x��:eQj���!��^���hd6{�l���Y�sNNΝ;wdB�0i;���o$  	�WP��U��6>��ޯg�4m�+����{�md���~&�=��~��jm��¸�>ƣ����T���Cz�T�-di���G�ݢ�~�������o���TWW���߿��]d�'��9sFR��a�z�Ww��UZZ*����n߾-#5��Giii����掎I���W�_A�}��'uIuddd}}��}{d*eee������;r�
�F���M�
!i$  ��H��_�-	pMq�5qS�����%�O�x�r8��Q�z���n��Ǣ�   ����/�Q;��p�`,�x`��ɁVUUUWWa_{�<�  !72^[yJ?�}���ʃ_�Ϝ4����&�<                      0�%�t�̄��ݦ!@=�{R�Q߹s�`7  <Y���E�he�3I�K��-�[�^�ߓ��-:�?���ۮ9���g���111�O�<�9��ɤ�������򦦦�����
���A�����}���5jFGGgeeUWW������_�|yɒ%jЌ3��fH{�{�9�������}�vGGGCCõk�v������O����Y�pa^^�4�����9��322JKKe%���WUUeffz�t�ڵ�nݒu�ꫯ���x�f�  j��������x�?]/�4L&g�{P�*sdZ^E�r��g���=wS;��>��C-�um�-�Q������˗wuuIr�p�Bqq�;wd�eee��jժ��^|�Ey��E���?Um̘1��xB��ӧ�߿/�j�
�s{�={V����U!**Jr����"�UO�������e2@�\ԏLII�z»�#�0�g��)y^�BV����K/OQ[�l��2��[Cb�t_�x�<��+  ڶJ= ������n:7�`���X�Mя���Z�X=�I���&=GO�伒0)��n���0)�Z=�ܭ���c�fp�dll�4�x)����H&�����,X o�4�9����2���7�H�Z�µ�Z�II��Є��Rf͚%/w�ء�nN,���&<��S(�pQ������D�5�&W�^-���i}��M��r�J�G�Q~HU3+�)�S*,Z�(T  -,�ulw�n������o������jM�'��2���P��2��y\��O�];���҃����ɉ�.�=����#�c�{�co�(������b���#��
��a��~V��
�"���I���ək]�g��y{A�^�
m�D��y޼y��۶m��ݻ�ݻ���z�ʕ�S�jkk��9��M�6����������]m5��U������۫��%��G(�LB�:�[__�ĉ��8c��1�Y�t���ة蜯09i�$�/���=ä8r���ť�fQI���<s��uYEd]H(r���#KL��;w���jjjd��:�5e�)5���H��3g?	��wQ����0�I=9]֗z�f��� ��7�
 ���4��FO�}U�X��^�"LJ�nu�_w�#mζ����s����)Ҳ]u��_N[�7�l����?!��s����{\�%���V��8�`�&�{�����9�j�.��������՚���^![C�0~�E|��U� ��z�]�h�l�7o�,ծ]�����|�(XZZ*�=y�dQQQgg��=>>��ڻUQQq�С�/�3����Lr�̈�E���W��ll��6LJ�T��zVV����6H��9}��g�uT���Ζ5u�ҥ�g�޽{W5X�ʠ�����%)B5	7,��?r~q&%*K�}����G���s��5*ȜJ�%| �@[|X�I��һ7_ӻw����;L�8���Xߥ9#ݵ+���}O�6N���B����q�K���.�v��Q���S�k����&�7^��K����0G߷��MLs%��_s��&���џ�=f�6k��'�8�Ѷ��W��l��ˢ�Y8LJ�?~��|�r�s��q�R6�]]]���cǎ�>���=�-��9�oFF�z�����bdd�����ݻ��O^^ީS�$>��7n>���+L�ȴp�B_o����$/{W�X�BԚ5k�^t3k�,Y�B��r�T���$c����'��8>��Ҝ9sdPff�Qy�ԩ�''''T�P�Yԡ��9�0LK����R��IJJ�5%�{ڴiҳ��F���_ 0О��3��j�{�n���-2�_�0����_��A�l�2{��O��	��*���ݡJv��GB]X��ӥw�xG�j*Lʠ��m��VQS�:6-�N�|v��y��`�&%�J�4viJ�]���i�ڲ_�p��#1�W^�d�)))inn6.DUA��(�m�4�,u��8���~yi\�������f$�1(�H�r�ܹ���g|�I��%�ި¤�����Z[[�M��}�����%QTUUI�=��ñc�dД)S�Ld�JOs5���l���Yw���eeeF��{�v����I(�,�P}�r&�J�1�\�zU��3F��}�嗵�3:����+  T�p}O������r\J�.�����
��q�@�����ӏ}������}MO�b�2}����#��jg�&��ϓ,x�}�z�����:�.��7���SW���ȶ��W��L��o�2��qN�ڲggg�{^�tIz{�֭['/�+M$�ݻw�m�m��M��gԨQ��*�$%%��USS#y���Z�t�Һ���ׯ�9�~�d�4H��y��m��.s���ߴi�$��R�J0V�|�}��1��܎e$��бcǪ�����ӌ��!��!�E���C�aR>x���f��Ȉ��y�X�>{^�b�  j�b�9М�4�ar�d�0�����qݍ�H$I潡w,��?���u/���q1��M}��TE���N�
�E��z.5��~з�2��%�ڲ�(�F�6��I4R���.A㰩����ݢ�K/�$/͛r!�Dz��`;Os����8�N����0�5	x��1��T���ZI�1���|ݱP��֭[�[�`w����АL���� '���C�a2..N]�3n\�`�AjsO�G��  P��������-:�=L�Lp��^��s+�c�O(��o���gR�^q��?1�&#��+����䌞�a���naR�������#���f�T��¤r�]����z���m���b7�6��D���风ٙ��U�	���L���;�'�^wvv�����u�|�Iu���plUTT����ni�$ۓ���H�CCCii�tgff��M�$<��ע�G�!�0)ZY�MMM潲
� ��N��x�+�썮��\�s��~�<���fmpñ7�����w�g�bd��q��c����b���9�qS�:yo����*�I��P�ڑ��o�{��ɰ��by��q��m��09f�~J����V{k��T��u[cc��������͛kkk�.�P����� �A�Q��9�~�Ʉ���[̻W�¤��o��*ݩؖ�����>��I�رc2�1c���_}�U�=vB5	3u�>r�
�QQQׯ_�$��ԅ��ty׮]}g3����+  ΈXי�k������Kn����3�U?�Q=GYU�w�8u�~�\�f��w'���M�_�-���O1��-Cznܢa���I������a&%��P�>�=}�ᑮ���ar�Rmo���E�����K\����num+�x�׋�����I@���=fZ��u�a}�%@�\��c�\;���Z��&�{�%�����C��x�^��(h\�m�^���޻w��1�Z��8B���u��<��Iٱ�i��n�����RݶQa͚5n��IKK��gܻRͦ'������nwݱMzƮ?�{��!��'�|QgffJ>4�5/���C^����ï\�����F�L$gJ��/��ދ/U �����
N��K�R�._o�4I�3��6�����k�~�\��']/�_&�t���\*9s�r�[݌(,L��N���iz�T7�\s�=d�x��\�3׺�o[a�
��e����c����zӿ��B���?�����*�fddlܸ�8.�d���>�/���j�xl�PRR"�u떴Aҋ������WS-X�ɸ��۷o�P�P~~���|�p�0y�����������z��$RuT��J���'����v���xlä:ҭ.���64�I8_���ۘ��~�,H@UOÔ.#�֪�j?���{MM���Թ��$���C�|��y7o�  ĸ���du��_��3~���~O�6�GF��o��҇�z_?���Z��C�0.�����w�xS�k��R��\����_�#�*��>ry�q�
��ZW��w���P�s��Qϥ�
�a2:N�nv�+�J>�e�N�ǑHƸ��z��'��)5_|�E_���U\\�������	8FM�0���S[[���!C���$��G]777�d<��6���9�0)$�ʂR�sJ;eY;�l�dbb���������%���s��y�=IA<dFd]Ȅ$v7?T��V� ���5�3	��:L��#gAQO�3
<��H֯_/?d]˒���W$_ �	�4W��F�ٚb��%n�~w��!y-�dрoZn�!�z<���q@/>r �'Ǵ��U-j�_�}G���=Dh�+//onn�N���� ��22^?}�K������+Nz��P��Iʏ�l���Ǐ���Twn1�\��  �$�[�%K�H����=� 9                                                                                                          fÇ���>}��`7d`=!�	  ��������߾}�������ڵk�v튍��v�'$e=!�	  ]TTԭ[�$xTUU�<y������Z^Λ7o��6 ���RRR&N�8�XO�l �A�c�����a�LNN�0a� �
   �����K�LHH���r���ׯ������\�r%55��x"""$�޹s������fժU�Q�ݻWYY�V?''G�Ϝ93�I8��ӧOw��z�7<<|۶m�Ti@SSSYY�L��ȝ4r���2h�ΝF�Q�FI��'O��F�_UU���^]]�`���m��t2������|Y���2�Y�f���.
  �$(,,��0c��:YYYR��͛��͕p�����Ϛ����-��ҥKgϞ�{��T�A�W�r����
���s��IOO߰a��0�o�>t��5i�d'	���#w�H�a���T���,**�� �:>>�a�ٴ����W�J�˗/�)//W�=& ��cǞ�mѢEC���Y�b�D�;w�Y���E7�f����:z��q<&&�������\M�(	N������ɓ'k=�Feff��N�*}rrrB5	�,�L��x��-�����D�Fn�H�aRR���I+�Φ��/_./O�8�^FDD�Zp&���>$�  �iӦu��k׮�P���۷���S�"����*++k�����cǎɠ)S�ę�FYz����e���K<���/++3��ݻW*K��$���---7o�f�e#�Is�&M�$}�9Ⰲ�:LZ����H^J�7*lڴ��q�
�P�_   ����%3H�hhh�����������.K�3ƠB��ˇ���d�رc�����W^y���I8d&���W�nݺUBWxxx �h��0)a>�
��i;���
�Ma�=�����an  ����-[�Hx�t��S[[��ܼ����h�*D�1��h�Ν+C%�I�-�p�I8d&e����w��U9���qݺu��ߢ��/�	���lڎAօ̸�-j�%a ��JLL<�ے%K�B��箢����Eu���wuuI8�~�
Q���I������R���̔��j��!��CN��-V�d*i���dZ4R]m>wT&4�¤����N��D9�C�c?p�  ��P8�k��S�N%���|��e�I�رc2�1c���_}�Us\	�$�p�h�իWK�����5~�FJ.����ϟ�=�¤�9�7n��I  �Ú5k$Ҙ����I�3.EQ񣢢b�ȑF���X��e���͛��s��{��!�PM�	_)+""��Ζ�w˖-�k�������쬪��ii={k/^��=�¤�������4R���an  �����[���痖��K�<)�:*޻w/77w߾}�����nܸa�m�SG��e����nCC2	III�=�e��TIzҿ��RBVV�ٳg%Q����{��u#Ϝ9��s;M�M	iW�\	m���M�1���p����?��5i-a  ����(������������s�<�����%g677���JĒĕ��b��$�[ ��ՙ�q�v�H��u�SU���ڵKp��}ɱ�oߖ�$A��	Y7RF(�Wf�����ѣcǎm���M'�6cbb�?n<��p   �!u%��M��!   x��Ę_?~\¤�@   ���˗KKK����o߮�����v�   �xؼysYYك:::���w����                  P�?�z���-�y�fkk�4楗^��|��������߿߸9uu�EM>r r����o��:(77W�ug̘�|l�_�111^�"�|�FbbbGGGmm�޽{w�ܹr��Al���qYݟ N����c?}�t��к����!Y �x�q�F{{�ׇ^�pA���_mMƓ��2q�D�C�|�Z���X�n����hr�qYݟ !	0���}ee�u��a��ԩS��7f��A!����5�����.Yxz\V�'@H�'�co&{ O��^��fΜ)��}��y5����ڵkZ�o�͛7_�|������C������Ǜ�s��i�%�CH�����l߾��fϞ-�w�ܹjժ�����v�d,X��\G�ƥa����fìY��-p�(�$<�O����%v��mY���'N����s�zd��ܱcǝ;w���jjj���!������+�)�SRR��vA9Y�b�ʕׯ_ommmii�r�Jjj��F����M�lW��r1b�|��ݻ'.]�4q�D���4�5�3iXO"<<|۶m��d�|���ʤ��P'�ښ���킲^Y��cǎɗ����Ç���eRm�ƍ�X�_(a��#�Y�ۏ��ua�6�1%_��u�l�2�M�t���+Z�����SgUTT�������ݻw�����̙3'==}Æ^��-Z$C%��P٦���<y��1�o���R��fH:;;�;�ȴ�x�^�*u$��۷O��嫾۟0)zժ�g����٣^Ο?ߨ#�U��СC/^����Z�r�z7���ٲ�$`��dY���:l��MƯ�,m��ʌ�x��vA�VYYYR��͛��KX�:�>���F����M��W��r(..V͐��|�����I�IȘ�b���a��#u��N�5'{�e��䥄L�A�M��ˌܺuKz:?����B���9�ua��s�.��&�'�رcO�&_,C���\L�>]�ܞ{�9�oї_~Y^���N�4I:v�ڥ����:u��]�/��nc�p�7�lȌ�����˗/�����ˈ���q&2��ގ�%''��Idd�����޽�\MmveS;a��G��l%�6��#9y�ܹ�`��l+̚5�����ѣƙ������dy:l��Ww���ʲ]��gT�+?d�
�N���]泚��"$�V}}��e����ܹsF��ǏK�����3c��GNsp���G�����Y�'ks��MR��,�fڴi^j(��<*�΅�ޗ������ѱn�:�F�7o���_�b���l>$g�����-((p�@�Isw�9�^�}#�лiӦIu��%K�}d鵵��7�Z�fw˖-�NW��>>x�@�8�v��6�.(�
ǎ��S�L�3��&=G����J0�;��t�be�.�H��O���	���---�+�z.Y����lW��((			�-QS�e����5�?rZa�v]8��Y�'ks��MR��, CS}}��s�����D�*�_��`��TuRSSKJJ$m���+&����>n�e�rI6��OII�i�T�Ӥ�$sϚ��nzV�r����w����ʶ�ʶ��S��{6�N�����M�,V��rP�7n���#�y����(,,��W�^ݺu��P~�y6���I��ve�P	��!����B�)Z�v���9��iA�I�u��#g�.��M x�����u�Ե�EEE�����(�� ���{����f�ҥ,HKK��/���ۨ:LZl�kkk�oQ�B&_z�n�{%]�~]z�7
j�:b��+d��޼�<_l�`���,����ި��l�����M�,V��r�l����<L�NB��';;��ݻ*�ȇ\�Uݚ��¤�e���0�f_�I	�ҽ~�z'ms��ӂ�����G�z]8Y� �(����}[�d�P��dF�?.1�ȑ#�l�-[����H�4��n�?��dEEEgg�yϤ:A��loo���>��s���6&�EWW�����ĞI���ʲ]�{&��233�*8_�f�^�ߔ�!oq;���I��ve&~���LZ����I���8Ca��m�I2N/	��'�4�7o�#8�)�o��ZZZ�*����ov�[�_���0��ۜ:uʢ1�I�s&7n��=x�L&�s�|m��LL������*���4��~6�XY��!''���I		n��������=�^���#�9YԶ�NΙ2L:��i={D_}�U�
�>r����Gίu�um���I�I��j�ҥ�y���Zϗmgg��I�vUԞI��sTT��P��0)[���ֲ�2��&����BQ��Z!u�@\�����V���k�L��z�Z5��%�͸ߝm������#Gubcc͛<�F}^��ϦC+�v9��r/_���.�_cv�?E������\Hu��Z��Tw����{//��Em+�0i�����������Y�			��c�c�.~�,օõ���@������G!�  �����i�vp��tվʆ��>��ɹs�|G�äl���e;7n�0��6-�I*,,���ظq��#�v����}&/\� ۲k׮��a����OOf_�ei��>Z�a��~z2���J_���lC�aRdggw��077w߾}2Gmmm�R�7Ҽ(X��ϦC�+�v9�;wN�����/����}&ř3g�{v����͕+W�Z��v��l嗝䨳g��bMM�繋��s�I�ne�$L:��͙3G�TWW˂ݳg�qWs'9�u��#�k]8_��u�'-�  �䧺|��t�R�OZZ��֖_�R�ȑ#�[����q���mZqqq���MMMj��l�18�&���9~���ϫ/�ت�'}Hf���t-S��Kv�aR�}҇l����߿/�ؼCú!	�ZϞ���RY���e{'�?���X7R	xu?�ٮ,�� 1@bd}}��'�VI������G�;v�_�Z&�F*KX���۷�Ǒ�ӳ���s��I��0�9�ȉ͛7����f��8���X�?r�օ�I��!b�ܹ�u�iӦ�n�֧y  �!���$Ǐ�-���`�& x�]�|���4++k���ꨜq�& x�m޼���������;w��x��                  �!�n�����gj߼y���U���K/��m�LAA��۷���ȑ#�������<9��ecj�y�ڵ ��Ċ���}aRs���8L&&&vtt����ݻw�Ν+W�I{�)S�tuuy>�TQOM�����p�¼�������N�#5�Cccc�]���������UUU����c���/Ow����k׮�u�V[[�����χ�����bI)!!�s1J{�W���+�vIJK�&�-��2�^fΜi�$L�IF
KII�8q�j�P4D��u��iii!i� *..nhh��?k�JJJdP]]����=�Ǟ={����gϞUu�KC>ê�$���]�t��5�e�i>,�U�/^����!��r0t����6/L��㼂�\8YY�dQQ�|*"##C� <�T�lnn6��0��f�O�!&333�}?��q1jԨ�����\_,"Pjjjbb�t�>}�3~�^�z����WAtt�͛7���.���l�0g����OBKK���+���Ze�-zdc�얃a�ä�J���9����r�$/^,�W�X�d� |�0���'�!��P==äl;�_����*ծ\�"_Y��|�He�cV�i�o3CTT��ʮ��jkk���?�|JJ�14""��矿}��l4e�'��⌡�gϖi�ܹsժU2���v���`���g�I#��˽B2R������A�fH�P����ر�Ν;R���F&�dA�h��͗/_�φ̅���)���F'�zZ����Ǐ766�������d�¤Z����LZ���ѐl#͘;w��
N"����~�z�v���C�KC��ݻw�]��֬Y##�Em��9s�����c&N֦��r�$�3/��.\p� �x*LN�>���kӦM��[������9������Uv�޽���g�}V��V�J�S577;ܦH������Ȥ�����a�I�.]2*u�� t�С�/Jwmm��~U6(--mjj:y�T�JÌc[�z6�4R~����K�R�{����̙#}6l��kK�l�dQk�);;[��U)[c+f����2	i��_)#��s�dAYOB>o/���Tx��srrdZ��
��F�RU;^��٣^Ο?��p����r���m��3g��׭mf!���ھ}��]�p�u;�j��ѣnIX�4�S-K��lpä�n�����߶m��񫂙��鹲�Z���+����1v�ؓ���r(Tp2#*L���\�|�8��&g͚%�)��1b�T�߳�����}}e����kc%Ҩm��G&g|���N��St䷳�ٽ{�z�R�lЍw��a�η�`=�Ni��;�p��M'�̅�H�'L���ȇA�e�%5�N�j�:"��H�e;�իW�{�;�^FDDܺu˯0iصkW���ܶ�B�XP�G&e�Hе� 9sɒ%�ƍ���0LK5�]�Γ��l�lPA]�+�jڴiҳ��F>�J�c0�^N�d`<��ikk[�|��
��B�\Y~-I�M����/�_��l��B'3b�I�R�َk�äl��{ʔ)q&����ѣSSS�C]C*_A�Ŕ�ֳ移g���6Hfx����{�|�ν�~�|�}�+]�H�t�R�9�M�4��t0ζ��l:i�L�~6m9����l��9�vA��#�$���(C

�C-��$T�1_��iӦI�u�X,(����z�qN֩l�}�m✓��`��s��9�Cթ�����ի2�1cƨ����/k��BX�k���ꐓ���L��1b��U�����)���g[��v.��,���:��p���a2""B6yǏ���I_g��ͽ|���
3j�.�W�w��p�����-�PZ�&��;S~/��]u��%_��P�f��b[�z6�4R	&L?��΅j����m��s@II�l��C��`��l'��|b>�"%%�;�a�v]�����1�/��B�㱍�4d!��3<m۶Mưa���k��hnnV���d�c0�0�I]#�k�`;^W�_KR}�Y�ƿ��Id�I�޷o_kk�ȑ#�a���V�Ux��^�F��=s��ŋ<x oT?Z�vU�"����4�p��u��ƕ)�P�aҢ��l�6R	&L?��΅�H^��g��f͚%1�޽{�Ӗ.]*����<ӎł���Thll4�E��a��]�łzd��)�ۭ[Ǐ��8Y�Z-��VVVJؖ/��kZ5��0w�c0:aR{�|�r l�����kI�8��8; 'O��dɒ�P�Ɍ�7����/�͛7�화�;��͕!�������&��Νs~�b���mϕ���D����;�0i;���TbϤ�ٴ�p.TK�n�mTAA�y/�����+L�Nb�L��\mЯAhiiq{�@ ,⇬,Y��m^�n�^�^TT��t�p%�B�����P�z.|�,���:��P <�S"C{Τz�.�1�����n���n�W�V�$Ϝ9�����+�8߬'���O&&L�Φm#���xN�:eQ'�s&�	���"#�.(ٴ577���u{�I�e;	u���9gr���7��9�_�#**����W��g����<y{ 7�JOOw��R��=�AnfC'L���-��-*Xυ���ג,..�}��`V |¹�I��$����Vej> �~�zխvvIu&ކԝg��Jp�.4�([F�ւƥ��s�ԥ��M-����i�H����/++��Y۫��M'�̅EF�]PjϤ��(�>na�bA�Nb�ʕݦ�����$�jn_�Bq&�Ucc��͗B�����A���5~�g�ʕ+����&y1b���b�(|-Y��T_}�U�[H]`�x��G6� ��y�d�g�x�_O���7�����t��m3���XYΗ��s����*�f�'�[�T��}��W�:�[�|rss���'ж�6�N���͛�� ��Յ�����СC�����3)����_F�>L:�M�F**`fddlܸѸuFRR�����Ϥ�ٸ�b�f3$�Z��H�J���%	I�999�~��6�+D|-(�IHä���l1���Ua���օ��<�[͙3G&a�'�/��Q�LL�Aw�)���)kPz��Ը�yl�֭摨�R�bB�A�}g~���Y��:����|����-�׻���Rgg�͛7�W�̂|����m+8���pI�gNY\���y��l��¤��%_,��ͭ���e���7�hNmj�[�ɖ����إ�z,Kuuu{{����/\�`�]�G��,AE��w�I���M�F*qqq�s���I-F��.��W��M�l��6#Y/������2$i�ȑ#29�a�ׂr2	�pΜ9��Lhä��P�H��m��SW �U�=��r��6�#����Y/����ˏ�@����z�zMӀ��z98�n�j}l«e˖��.i��D�̿����Ӝ�l+8�ە�dI��;  <�l������}��O3IY��!H����37  �#q��]�Q#�$e555UVVy1��b�
��2}���n  �9s��ڵk�/-��;lH����+W�{kz        0D<�>̺v  0tY�E�$   ,&  0�$   F�  @��   a   #L   `�I   �0	  ��&  0�$   F�  @��   a   #L   `�I   �0	  ��&  0�$   F�  @��   ��E�2�                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        �����w
�B�P(J�eR�b
�B�P(
ů�����M�:���S>3|<�B�P(
��H��$9j�#��1
�B�P(�Ǯ$�H3�L����Hs��L�$^�S(
�B�P��2"a����ć����p���i������P�|�/�����>���31荧P(
�B�nyf�$Ϟ��c�n��/��f�7��y#�j���
�B�P(��P>;b�[�O%���8�������Sj'D}Y��<���qu��3����yX��ڠ7�B�P(
����ħ�8F����U���������?������ 9j؟�AJ��g�K���'T�o�oS_���P(
�ByL˧��?��p)�1@�����(^�"q�щY�"b�*��0�5^z� 'y�?/���H:�!�a갟o�+ɖ&��3�}�5��1�����A_
�/I��B̧���
��_y�c"b����7��ץC^�T$1>��W�|J#�Q*���=Qb��c&�K�7��S�_�ןy��\a�聊�
��Q�>1�3�e�㞎�wH��_�OKGd�3���+��l��im��U9|���w$O�%�o������鈱�=�
�+��$@���T��=O�Ҝ� ����"bǫ��$�oxL�T��%��09-a��/|
��d��/D��?-l�DI�1��$N��8jܬ��i���Ok���M�7c�9���J�}�����O=�8aƬ���*,�鈄����#b�&��6��#��KmD��7i֧>?2"z쌔O!v��B�<A�Sa��$iΓ�a�P&=p[����W-�����������GG�0�ژ�A_�
�I(O�',]�^����:��_���ko�������E�ۼ]z�;pt����c{f����/���5�|���ӿ���~��Rz��9�I����;���q���z������%������?*�~���8�B�<�������o�xf$I����ޔA�����h&?ӛ'?��OU�#�$y���?~��s&7>s�sO�*�P(���#LF~Ꙩ������?����է>7A�U���B�CGO���4y�o~�[	��0����M�5:q�z���]�����o�9G���K��>g��J�P(!,��������w#b�TT��7��7��5�i&���F'����N�P:�e ��1���a�_t����g&���w
�2�����>���o��]&?�����w4yƜO�'�G�KwyE�S5��z�t��7���R����x�Dѧ�����H�ɿ�\����~�[�=���ڻ���紑��YR(���O�%Hh�b��(���x�_eo	 L�$���C?��#)�!/�͓	����߉��{����̉z�~دb�렯
���.OG�M��X��nU�.X��_��_T���3Q� �_���o?����~1�?��?��կO�������-;�����O�0}��-*=:z��_�t�X�T�0��o|�/?7����I
�2(�&����:�[�:g2��<��_<��U�L=4�?���uc����f؃�� E
�2�%��/�|���w��?��Ï~"a�/?q�������x�D���{���S5����?��ORs�����ۿ�R�υK%va�ۄI
�2�E�v~t;�0��@�h�3�';��gK:�ll��E��el�蹷�����q~�Bؒ��3Q�c�����c���ꋣ$>��t�ا>��/�Wa��1�3��g"�}�1����	��|�� )�%I�q�_���"�z&Z�b���$)�#/��n��F	�0���i���F>?��aS�IG��vB>������aW{8}���a�9�+K�P(�H�3����#����S(�c[$.~J��|��gO�%!,^"�Q�?�w����*	���B�P(
�B�P(
�B�P(
�B�P(
�B�P(�                =fj�?�W&��6�9����ܣ�PRRRww����   ����}qqAV_�G&�L�V���4h9���*m� ��	�2������򦦦�������;w�1"�����dPgg����ɓ�[���QXXڙ��o# �����/.�����O׋ļ��ک�ׅ9~�!v���M��[��>��^׶�ҢFHk�G&�/_���%	����w�ܑ���EDD���())��uuu���w�����/զO�>@s핿�  j[���~Y�{�]-<½��C&'/�N��H[��Ō���[	��s�Gc��{�+�YTʘ���>L������/�������顪 RSS����Ӷ9-**���I�](��~5  ��p���z���[;�c�c�<�:�ar�Hm�I����@x�-��y*�ʘǥ���~۵�p�,=���e��~�\wQ��,�\�jތt=/��&-Ҟ��FO�kI��h�޽UUUmmm����ϟOII1�J;~�xcccKKKqqqrrr a�z���۶m����IHH+++۱c��ؖ.]*mؿ�@Tp�Ӷn�*u-Zd����y��˗/���utt�������x�lg��r L 0�渒��	ڡ������X�ɈZv��.��is��������L��������rڪ�Af3����^p4��O�@������芊
I&׮]�pu������K�.��o^~�e��/���HMu�د0i=	�o�>54++K�|�ʕ{����Ķ����~����`��d�ܽ{WfA�c�>|��Kf��ɓ2�EEE���RM���l:_�I  ���z;��޽��޽��G�ar�	נ5��.��]���Fĺ��\N]��G�8�%����]{Ũ�ڎ�ک���o�c���8�	�j��N�n`aR��Ē={�}$#͝;�5�W��cǎ���n��7LZOBHd�њ��:�k������w�ԩ��Zۍ7$����b��V�X!6l�`�)	s�ԩ�>�/�j�g��rp�H  0О��c��j�{�n���-2�_�0����OC_��Q��M�>#\�4��l�>�w�*�-z�������.���;z�Tc0¤Ċ�q��t7�.12^ϐ�~�C_Ֆ�kQ��X�[<x &22�k���b	-'�8ߴi�_a�v�����͛��Y�~}w�s��EEE���b��$�644�]n�T'9P�SPP�|6�,��  *b��'PߧwX9.�w��~�|���8/��ein_����cߪ�ꢾ�G_�ӣ��L$yR%F�3S�dd�����=W
�Ԛ��%&�e����H���o�G���O�Ə����
�.4�}e)))~�I�I���B�s��խ[�Ξ=[򘯚111K�.����~��ȑ!;�sZjj��^V󠒒����n����;�M�ˁ0	 ���H�5���;L��l&W�����m$�$���;d�˟qS\a�ȷ���ѾQI
��I߭j�̸�t9̘1C2I^��٢�jkk�}&M��W����1bDvv�ݻwU �)�[�΢�ܹs���	��uN�p���6z��ݗf͚%1�޽{�v풰�`����4�/��|6�/�$  �K�א���_�E��ɑ	��۫�݀nex��	�t��}��3���>h�IW��dW�L���9�����o��p���@ߛ������� 7'��O��^��]�8�v����	՞I�I�%&&nٲEBTWW��%0Ҫ���`��d^�a��fꊞ)S�}����¤�v6m+& \��C_�fot���˱�w�~v�+���>�co��s���i7E?B��Ku�V�g�/7Ι��(u����$/UtxΘI��zE]ͭv���t9'4z�E��1��I_����u-�HHH�
���Q�"�=zT�ݤI�<���477��,Y��W�TlgӢa �A4"�uӞ���e�W{ɍ��zf��g?���(�
]����ԭ�qs��qC��d�X�Bx�~��T8��>��;=g?�HK��]�BϴzbB������a�dZ���s�a�m �I�ޕY���5�K����')�/55Uu�\��|�:""B��'���}MB�it+�w��˖-S/W�Ze��9**��ٳ�V_��WN���mmm�՞I�]2	������i[�I# �#0#ݕ��7���u�����MWXE]I��k�~�\��']/�_&�t���\*9s�r�[݌(,L��N���iz�4nVi͸w�[���n7�<t�Pee��>�7nܐ��/_��RS�W'��L�MBr��I���/�Sb^WWWMM�q�tII���u������]�=�4n	|�瑋'{�S��zi���祿��Ff�gϖIȘ%9���ܹsG&d���i[�I# �#��
Jq��Y�����������z����z/���Җ�τ�����/��^��ݡW����x���#ћJ]cX|H�j��,-`�q���[��/�1��_֟��/�x����������_�p������3g�Hj�7LZOB��]�JKK�[[��۷e�F���(--���@�������!iV����+h�����.���������o�L�������޽{G�Q�����i[���  ���4W�[���j��w
�?��M�ᄺG��ի�!   }���/�Q;��p�`,�x`��ɁVUUUWWa_  ���<��>�}G��/�gNdtno��                      �f�?Sf���n���=����ܹs�2ԙ�y^]]mQs���R���ӏ�m��Kr��� <qS���I4�2L���ߥ|O��ӭm���I������s�mל������ɘ��2�<y�s�#�h&%%��斗�755���TTT���:���N�Kmm�Q3:::++K�A[[[}}��˗�,Y�͘1��.i����s{����O��ޣ��npä��rQ?Η� �ᑅI�������dEwvvz>q>666##���T>����UUU����w|]�v��[��3�ꫯ���x~`��  ^���w�������Ebހ���~jTea΀L˫�Q�S�����nj��҇}�彮m��?���0�|��.��]�p����Ν;2Ų�2��1_�j��^/���ڕd�ٿ��6f��o<�[������[Ua���۹=Ξ=+YK�H�1!�1��u
KII�8q���k3�E���.�Al��&KJJ�����&���#=�� uU祗^2?�~˖-�S>*�Mb�t_�x�<��+ �/�*��t���ߓ����,>4�ar�b��7E?Җ�j1c�x&�VҚ�=!���J¤L.�Uχ^ä�j��r�2f��1������� �lȊ��d������j���FI���Ο?/���y��$�+\{�U�4�-LHHP��Y�f9�a�#����~}IZ��q	��������!�m�0�z�j�}a�~����y�T[�r�1u�U%YT}l�#�S*,Z�(T ���pױ�y���?�;��s�c&��ԟVs�kz <�yWχ�d0�Qe��R\}r��ڹ7v�\卞ON\wQO����Ӡ{S�D����f���������V�C��;����V���wLZ�=L�\��?#]������Uh�ﲚ7o�|-o۶m������kmm�r��ԩS�
����߼�Alڴ�����^�o��j���\�jUUUU{{�l[%��G(�J"��۷;::���O�8gu27K�.��;��&'M�$�eC�덞aR9rDz��r2�ERt��anَ_�~]V�l�emJ0�.I۵���E�G�9�%i��S������+J�� �RRR� i��͛/_�,!G� �����㝷!��!)N��LB�uSSSYYَ;���M^ä����K5�䫗k֬q�5s�L�7�
 �K�WL=A;�U�cY�{�0)y,��}�鏴9�z�?Wύ�SB�H�v�Y~\9mU� �k����6�]�R��qU���[�㴂�W�\tP�y�zw`�L�-��;w>\PP 5�*�}B�å�����իW%DG�IwѢE����T�v�Zz/c��6����2ړ'Ouvv���[^�w����СC/^��9SQ����dC/3"o�횿�W�����~$�0i;�E�3g�,�6�ژfee��z��A�Ie���}�Y5�vIڮM7,��?r�Y,I돜ֳ�M��� QY�*��t��N[�
�D���ݻw=[h&������S-��~����ƍ���Mkädc�&S/�=*/�ΝkT�ό̦,�PU  _�cұ���������=���+N��)�wi�Hw�,�~ߓ��S.����w���`��ˮ�}b�xm�m���Z���I��W��&%�.���m�$j�\����\㟽�5�%G�g|����ڠ��4Nh��`�&%���(d���?~��|�r�s��q�R6�]]]�cdcǎ�>�������M�q�ߎ;�OFF�z�������������w�v8c<yyy�N����q�l��] �¤�L.��F�0)�N���9s��1l��� g֬Y�jd�k�֓�RWW'iD�t�$m���C��s�ג���i��e�ٳ��#KՈ4���潩b��ŞKҢ��_���n�2��52�!����a���X��pUNJJ�����;m�4�YSS#+T� ��|�����|�ۭw~�EF��c&�^��K03���Rfor���:�P]eS���;T�n��H��r�����aR�A�I��M��UԔ��MK�S/���}m+|�I���!�]�n���gZ:���.\0�Ȇ�W^�d�)))inn6.�T�<��q�aҜ|�_�@����qQ�ֳS����-Y�AQ�הs��EE���8�+L�-����U��p�����󭭭ݦpl�`8L;vL�O�2%�DV��=Z���pI�Ə`u�>rN�Z��9i҃$�A��3rd9K��q�O�m��B���؞8�(ä��������ի�g̘1j���/���W�X��  ^E���;��/ǥ��B\ޯ��0�� �*KM1a�<�ط꿺�������(�,�I�>R�vfar�^�<ɂ��'1�g�˘I�#�R�|S��9uE�ˈl+|�I!�$����.���tQ�-{vv���K���l"��u���K�:ٖ�F�m��m����gԨQ��겔��$�jjjd��pn-Y�ti]]����G�i��2L$I�V~۶m�eΏ L�:GN%L��t?[ԡ��9�kI�~�Ə��<���J����0/g��6�!
��ĭ�[���.�G&���@Zh�Dˈ��%?��z͊W  �&/���yO�&�L�
�+M{��n�F"I2��cAV��7�/L�{��$���go�E�*>���N*(aR��H�S�A�^ʌ���k��vB�:S�8^&���Ԯ$��$'��I~]����|饗�y$$�HO�q����s�v���S�Nu�y���1������]����:\�~�u�>rN�Z��9�6��<N��5k�,��qw��%�Z�pZZ���^p؆��/Ĉ#$�߽{WE���F��nz4a2..N]95n\����AjsO�G��  ^I����w�����092��{���έ��>������ƞIu$z�IW��dW���ү�Vߓ3z���b��I�����V�G��|�K�uRA����w�S(�W���^�Y���D�i3�H�M��QG���ӂ�������;�'��tvv�����u�|�Iu���p��!�=����8}q ¤��:T9'��3i|�ԞI�݌u��߫��Ǉ6L�6�Lr��-[$L��-�=�0)����hjj2/�p u�⡯h�7���r����]���.WĚ��}�����~��}x��]���Fƥ��q��3�M��L�M��佡�/H^��&aRB�kG⃾��i�&���h��*.��V0�
�c&�(�jn����=/K�+_'��V�\m���Rm��͵���S����RA�� ۍ��s&�
�			�=���w�|�IنJ��d&m�`�~�����jQ�W����ﶼ���%i�6=���C��s�גt~Τ�d���4���y�������իWw{\Y��ڴ�+LFEE�<���x=�#==]޵kW�y�n�)�W  O#b]g�5����Kn����3�U?�Q=GYU�w�8u�~�\�f��w'ƌ�+�G��nK��o�S̼�w�Є�Pu{V�Wr������a&%��P�>�=}�ᑮ���ar�Rmo���E�����K\����num+�x�׋�����I@���=fZ��u�a}�%@�\��cf���Y�ui�[��m�le���s�@��}eee��l7��U����ս{�:êU�����M����0�/7-����q�qY\����z������k<�¤ZP6�g0�����a��X��uff��C�^:�P}��$m?rZ����s�I�M;՞I#Y�rP���������7�DT�޽[*,[����bm��k����+W����n�d����LY���zu���ŋCU <�Hw'��%k�[��7m�$�WXE����y?V��䊓����/f��RJ.��9u�ޭnF��\��Ky��4=I��U�9�2O��?L.�ހ�k]���0u���2����1݊�g�{��߃�N|�z��tuu����:*WXX����q�F㸤� c���l�U��Dd;���iح[���^�y���|5ՂE�����}���	���K�%�=N�:LZ��0gΜ�G:fgg�ٳǸ�JRR��O����7�;� ��¾}�d����IM5��>^_k���V���IB����kIjv9��>�RM֔��eIJ��,����{Ցz�0���_H���}4�,mI�Ҥ����V�Z�NH�W�Ugfʨ�Ku?"�w�)=��֭[�1�o���C�|���vF�W  7ƅ-n�$����z���Ӵ]��{��q�82J�cN�>���������z�q)��w����ěJ]cX|H�j��,͗�H��iU���˻�30U��Ժ򔾓PD·���=�z.5�V���q�t�[\9V���/��p:g<�D�t���W�#Qwrs#=��/��kT���������{x>Ǩ��TO��������2��1���I&��uss��A�#u3Y�I!�qYP�5i�,+c���Coc0ۼy󫯾*��<��x�W����_6��(dmʄ$i�`_k�����!��9�uIjv9E=GfVV�4��=��(��ʤ�ݏ9���g��Ն��/���w��%�Z�&?�wʁ��|�M'T���.~QgVxr[�ׯ��+�Q~wH#=�n� `J��_\#�lM�~E�7E�;Pؐ��P�h�7-7�F�E=�L��8�9 ��c�J����/��n�"4L������777v'p��G �D��>�%�Xy��A�'��r(�ۤ?��_�[����gff�������# �'��]���������U�@���     ����0�2�  ��E�  @��   a  �K=L�Scc�_㉉���t<F�  �_*L޽{��y�G��k<��O �$  ����"L~& ��l���ٳ��Ν;W�ZUUU���^]]�`��Byy���۷o7�g�ʕׯ_ommmii�r�Jjj�ۄΟ?/�رcǝ;w���jjjd�N��h��gԨQn�6<<|۶m���Ҁ�����2���x�i��
ۼy��˗���:::�o~~~||�QA�~�رk׮I>���,����߸q�_�a  ��a�,--� &٬�����S����-Z���.1I�IJ�5y�dc$YYY2��͛��ͽw��g�5OH���l�a�.]:{��ݻw����p&��ۧZ(�9p���0i�y$A6�vA>\*TTT�����K��=::ZU��2e���H;oݺ%=cbb�7Ҩv��'K�@�  �2Ι<�ߦM�T��$�L�8Q�ٱc�����0���0��Y�����=fT����Xe��r��d	�Oxx�9�Zp&%wI03� C�H�%5�N�j��ŋ���ܹsґ��,�Ǐ��H�ܹs�7R#L �G���ܒ'U��̻.'M�$}ܮб�ǎ�AS�L�3���s���F5�Ӷl��\8	�---7o��5���pAi=�266V�/iV*���}��a�HHH���^��Iҽr�J��zrl}}�ŋm�a  ���a,��gN�,ä��*U.2���f���0YXX(}�^��u�V�/�.��t��RSSKJJ:::��q��ҽ�~�d��{�����{�ڵ�0�$  ��p�>�����������j�9mĈ̅�Fʘ����޽��Wcc�u�B�H�6̚5Kb�{�v�ڵt�RsZZ�Tx�T#L�7�0���$��ׯw�Ȁ& ��A�,//���>|�uKTNs�a��4yoff��GA���e�	��*���i��


�v!����&62`�I  �P�����nә�f���2hѢE�-	&LJ&��8p��3�|_aRY�z��B�H�URR���l~˒%K�
�0�$  �W��dXXXkkkYY��1TTT�9��k9%�0���YUU��\�r��Es#����w��-�-[�F:�3i��6���
�)233/]�d��L�  �_��(Tbq&�ޠUXX����q�F�mp����{n�����o�>�����v�`¤8s�Lw�e���W�\17R������������:{�lWWWMM���� i����L�������999w�ܑ��W�t�H�[ �G�׭�D\\��O������MMM��nO�Y�|yiiissskk��8	u)))�
A�Iiչs�d䍍�G�;v���2�]�vI�߿/���������$�F:YPiiieee2rI�G�Qׯ0餑a   �a   #L   `�I   �0	  ��&                                                                                                                                                                                                                                                                                                                                       <����`�
endstream
endobj

5 0 obj
31387
endobj

6 0 obj
<</Type/XObject/Subtype/Image/Width 879/Height 615/BitsPerComponent 8/Length 7 0 R
/Filter/FlateDecode/ColorSpace/DeviceGray
/Decode [ 1 0 ]
>>
stream
x���1    �Om	O�                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           ��@! 
endstream
endobj

7 0 obj
547
endobj

9 0 obj
<</Length 10 0 R/Filter/FlateDecode>>
stream
x��ZI��8��_��@2Zlن`�_���̡��,0������)�"�dY4�Y*�j�j���^�����\�͸�2.��M�e�m��ǿ�����o4�������5��|��r[������_��b�����w�\�ݼV���
���i���fįv�Z6>����~��Lsqł�WЌ�N2��3���!�g���D"į#,&������/����	��:<�'z���L��3���-���#�q��/qW���8�9=Nk�0�MfsǮ~�wؓhMnʫ"� �`�s��{�(�֑�v\��30�L3���=�B�l�M�a���t��:݅��Ө٬�'���8�t~>�u��۸��Ig�w�\N�5�f�����g���z��;�XZ��		��˚`� \�G�Ԫ��?��i)az"�h>i�7��!����$tD4A�J�Lه�tѸ�
R{�-�@B��_����!������/��8�~�@ �	�
����g�k��P-r}��i��i��4�N>g�=;B6�99W�[k��I�����,=�5��ؓ*�j�� 0&1�7��XrE6�����I�� S�Č�tuB˥E��ܲ�HG�l��䀸N鏅���������d?QH�Z ���"b�0D �9�`r]��D�� �2#Q�8��ęFw��h���*�}()G���j'��$M�
�Vɠ�Dypt" (}ـ {�b\�N�q[P���>@=JPh�1���L|�堑������h�i��9��:�Q��?�Ւi ��X�Ӌ,�j䤁�����x���#)�f�l[ �K؎��0�@�׆��H��&E�?Z2���a�x!=��$����-\ �;�f4��#N"\r�b��9[�����Ϥ>��Ňr���*��ϥ�Ş��X9����ʥTCU�\)>�"iG|��!1T���9#�i*k<O�4juXs�[�ڮL�����~�?�m-���"'�k����lL$^Q����(hx�؉Sm�CU�H���3���DFd�w��3�e��b�A����ǟ�ش�������e&�3�O^OL�0�,ј5�� �F�3x �Qذ�u>;Υ�$��$���t{��jD�ٿ�:�-)�W���#�����X~i�UH����G��r�ɼtbUg�LC3Ei���U9L�^����"(����H��76�����U�y_MPt�D�,��8�J?J��c��6�K>�+�Ed�nA�'�
��9i���bp>�d��M����[��pi�M26�	x!�.ʈ!�*�Y�Z[������KSS��X��žC�*`�ڌ���ܕ"yMJ�sVH��*jX���zo���)�sY�Z)cuI:g��C�b���D�/�b��8R��19��n�!���Qd��|�ફ��̦�D��ʷv����p�U��oΊb��OXԛ�U�^}oǩDm�m\toy�ċ��)b��y���vΛE�R��ڎU��Z����V����U��f�%{�;�0K���r���v#����<{����{�n���M�2Y`2�v�9"L踥�B�]�$�Zn�
\����'�1u�9�I��O���	8}����%�<ӂHέ�׺���{���&J'U͞ʩq���z�C��
�&���P��0��"�i��������}?�Ď�
����>AN Զe�>&����{ ���ؘ!����Wa.��V�2AW�1����Z�o\ަ+1*a]�r���5[^���>�������]ίj��@�/0�<�;��y��F'j���%Ӄ���@<�.B������,E7e��䓖�ę�z��l䋵]���ʚ,�0���!}R��5`cY��?�ߕr@���;�b���ќ��X�0*��Q|�/�mF�E�ة��(/���2���G�^#'��4?��8,f��S���=7��f�\]s�\�F 汃kݧ�k��F�/��;ܮ�ĩ�ಬZո���-� l�8\$�D��=��mHj�h!��Ӯ�#�3�.dȌF������/���u�vh�G1@�w�ަ�3��;�����CLx�����3�X�x�s���O�������(Y��/Ž^�v��`ԅ���:	J\�ʵL"��~�ԯ��v��>����M��X옲"�71�!_%�[����y؀WW
cզ���W9��Ɏ�Q6��T���BhT�u��m�v6%Y���ݹCW��)wT8F�!2DTV�6�fjQY�}{��λqhp0����rV,D��M��p^[w�J�A;@bgXHs{R����m류��_9�PW���tR�M�X��pV�v҂�O:$ug�x�D͠��@#^J���N��,�t���S�I�=��"�*Ծy]�V#������;e7uy�#}�\1o���s���U�W��JG���X#�~o(�+Q6܋��}���9��Tc�B�&@z�Iu�s��xD%�~�PUt^5�X�T��\�[L%d�O!�wN�`��/��?�@	
endstream
endobj

10 0 obj
2547
endobj

12 0 obj
<</Length 13 0 R/Filter/FlateDecode/Length1 23452>>
stream
x�ռ{|Tյ8��9g^��9�yf23g2	��L` ��!$!<�f@Ȅ<H����
��%U|[M��k-�:H䢵�����k�[lk՚^������k�JN~��33� z?��~��&�9{���k���^k�5$zw��',�Zv4�ԅr�	!�F�Zv'ą��1=B���=�v<�/W�'�"D7�m����?�'BL�,�������{4L��VlcNn���a�!�v�H\s����alӴ�����w>"d�Gn��|MO%w-C��̋]�;�
����Ob���ݗh%��\�R���ֳ�/�h"�@����<h�<�r�No�1��+/�r���������1X*,�2u���3KJ�e�fG�+�̝Wy��UI�����?�;���k+�ߓ>�1�!�2��3�[^9�����Ы���cd��A^'�Su$J:�.�d~B^E�򉒍�	r�+�=FNa��'���\�%���_'�%;��8����0��E��|zry[�a�_�)Ƃ_�4ٞ}�<�"˙s��_)a�ON��`���yޑ��/5z�܈��Hٍi��,��b�;��F��|�,&۳j<��9ȿ���'N��٫��3vf�M���8w�v�WP��a�3Lg���R�L9�ʟ3��ϳ�$��M��W���m���&._��{����~�ہ������r�f��1���HK7m�5�oX�vMt���W�X��~i]m͒��Rբ��_V9oYe�Ғ�ӦN)*n��[-fc�A��j8�2SLB�6��B]s�6�\_2S�uwԔ̬�œb���7%T_OA���S�՜�'%�l�SR1�&���@�"$&_�	��`�FL�Q���h�r��Ќ3� ֠�RF+�&�vw����1gIhI[N�Lr<ǈI#���B=�a�"�	fZ�e��7+��Lk�[��5��5�`0V2sY���Ed	m2�]���&�Ne��x|����O�dk���jm��1�6c݃l����Bqrz�&9��sn�y[rf��6Y���bm��]BRSćă�Ip:�ޟiNA�E�%�d�$amcP�x��օĺ��ͧ����D>t��t���M���ĩ�gy�u�ǒ|�.���^�vE2wͦ�$ST'v4#�U���A!���b�dA� ��A��NId+f��kռH�z�"R�8�d�J�p�ı^)�O�d��C���&��e��Z����d�V���Ƅ���So0t�&����qT�Z;Ťf
	keW@�Q��i������Llbe�Qک��S�vw��	]_�
BCcR���Ԝ�X��0�h�#�:k(3��PO���pWVm�FZ%U-i_�$�T�d���+��`�F��VhM�3$2>r�\����r�Q��KPʦ�llmO��V\w�b�7��b��X��-��Rh���
G��JC�u�k66�KD-P��j/j&��U�AL��b#�ec��#@��D�z~'uEz|x$8�*�[�@l/Ic�0���ڶ����ԨF�%��ִJ�YR�Ƃ�d&��b�c��W�Z�.B5�z��%���ҭ��j�BbR�6*sS�C��"�y�W�rY�B2� �3
1�u��l�&��|&[Q�t�xPZ���x(� ��/KE��y���eA�P��<.i���$e1w\�4Z�z0��q�F}r��:�/Y+�Kf�j�>�[����u���.����)�%����B,k|F�M�B� ���d���bFO��H���R�h��
ӧa@ZN1*�W;�B;��%�Z"��9��UX?���q��L��Hz� �3�=
�)�<�v��	��{k���S�� yU�~Đ�޺~���O�pw��o�Z����;�ٸ�Ԋ�����8�)��8�5��Z�l
-hMɜP[u��V�U
�J�k�E�������$(��1�KR���� ��©*����%H�����w5+��,��k�|���#9``sr���C��6��b�D��H�i��b���BD��*ӈD�Ip�+74�B"#���9Ua��V~V>[���Qm��<��?��������7��l���������?�ߔ�mn�/���DQƨ��1��̑�ĤL��mg�b�\��)f��$7�nعs�2J��(��	<*`X>��U$P��?��������^eC�����9��?����W~W~�9&O~R~B~� �/��vw��$���1�XV�7��<����g����lԺ�Q#��<cd]6V��#AZ�H�Ƀ�<H��`T��f�!U�B�H�])V���R����J�D��C �����Ԋ��]*�n	Ɏ!y�cp�������w��x+*���y8�BE�[i~5��qA��g7,��&'���y�x�`0�ll<f�b66�j�6�̶�y�7�� ��<x;^ȃG(d5���)�
l�h�T�he�擴�^Z'@!�-*Ev⧷7+C��I�dU1��T��|��/�RJ�f�F�`׆؍������ʫ^{�c�9��_e���������iɻ~�[������$��r��f���Y`�ђ��rm���X8rsC,��~�����P^_,�c�}�]����@�c=�L�rad&΄�L��:%�yx�fUt�E�+�L畞��2�V�3�ILe#.?��*ʧ��b�"�D�@k���"�Lu~`������꒩�}瞃�>|x��]����ꖁ����o?yv<�oŐ��Sx|�m:�Z���������'�'}���g�x�C�i��ԣ�B*���h":^'�X��r�D�j�b�[21��	M7f��T��2�!���QEdO���(�0}`C��1(�RN�5W�Q�{:
�}��N�H%�N&�ép=�E#������oՙrL�X���	'HNؙ%)Hb\WJ��[�l**����nBN\HA���f�6��r��=`3,xy����u�U{JJ<��)�5�Ju�DQF�pl�O�6z �W�:|~�Ƭ���1���fsFq��4kb&��~�À���ㇸ�~ ~X�/�e~���a��!RZ�S������S@�fN/��
�\�BS��9((�:��S�[�wۜ#ee����K�~:�{;���+�u����6�@������}-<����+s�+�$��E�d���o�l6�;ǕSr��h��5�ј����kb��g��U
AH*�B0�a���@�JW� �ȕI��ӋLpOIe-sE~rS��t�Q�Ou��2�������]zf�ˆ^��K;۵Gei�z��]�bW]`�=%sg~�?�?w�O��ᰛ]5���� (�]��}
盃{г�M��H4���[�1=�أ1Ɖ�nC#n�����Fi���ݐtà���7�ݠ�WXe�#��2
�iAv�AZS���i�
�$Y�P����S*����:�'v$��)������o�0�[n޵�}���,�x���O�y�ǧ	]������&��Rij�Ţ�eY��3q�tF��aM�8�3�rCح�2��"�4�p��U��	�
4GHPƣ�)��7]c[��~7��u�}��m�]%S_{�al��j~�;@ǃ����4�ʃ:{�U��� �r��1��g�ј�u�π��� ΀'g@�X=�r��7%c��*'�O$�h�L���pl�a(e(	]�/R4t�Y�7��O���Jf�����ڮ����m�gT��Y���6�L�o��޻����}����^���T�ʛ]�d����-���n����g�\nM�3��rhڮ��y�����TB��S9�%C�� #kɴ��٢������Z�u��٣�FEKNU��0��7l�D���>[5z��t,���)����d��J�3�Ĩ�\�s|Os�%>�/��sF�������X�Ê�d%�|�0��'ø���"X��� ���p �)DM�)<5�ԔT��jc�r�*҆D��Cה���P!�������{�pv{��a�IȟɁ�};7�z�u�O� p��w�|���^~�GS����0�B��G�F���6�L:�����Dc��\�8ݸ?96�d��1�?�s~8�T֜*1s�	?����5~(�C���w&{����2�I��v6e�E�S�����e��TSۢ�M3[$�\��ˮ��W���5�7޼W�j�N0���:0v��E2��|c���i�y��K#�k�&�V�m��Y�nh���3�����fh0C�D3�f��0j�3�5�i3�K��Ph�sY�f8�n$�F+�hv����>3$hOjC����a3$�0H����(�L-��LQ����K+�	�	��)�Z`(��:tp���_�c�Ǣi;�"O���/hv!����;1��n���sq���W�u�o#�< z`����Pe�.
�&�$RvI��QQ���;*�*�7t��>���g���?�ߗ���|q�
�$zZB��1N-����]�O�os��t���V��8�nr���Ml�Y�����z`�h� ����{��@�y�ԟ.n�@��d��)2�p£t�t�qDic&4e�`��vʴ^�J_�*��4�U)���̮����-��^9��~&�S���f��?W�@=�K�z�	@o�q���aP��X�DP�و�$� 8〤�v��zM���Z<@ӣ4;L��i�մH�e��e9M��͞��])	�T��8�BPu��2�[�:�0sr��V~#/����\���.�浿(?G���-$~�+���n���^]��Cu h�������y�Z�D9�9�5rr�I"�"�E��}�	�6k�Tv�o�3T�sх��#(́w��Χ�>7�?3��������7]g{j;�?��_���=n���oػ�������;y8��A��B�Ja3��X�c��^ca-�b����ӂ[��0�� q0�U}����,7Wz���0���ƞ`�����"�S��a�~������c�U��|�P7) �HK�F"��Z��E���'���Hj��5��9`��33�����tR!�B)��B�f3~������lbO����VV����B%�-WY"P��o<S��~�5�������!q���c���s�%x��k�q��ײG�G��<(?)?X��5���7�C>z��H(s�ǹ�D��%Ed�T%苊8�d�p��)E9kbn� ��`N-u}�S���B����?���40�y� Vf�LI��"yJ	5ppRB�"�R�jem���)ř�W��.Y��=�����X��u]��G��|K�ᚖ��O��ͱ���-���r�b������C���l�J�ʺ)V��	��)i\0i��dڴ�����̞U�ͲN����h,`-v��1�kc~�b8)���l���F�m>�������#p4�D`k ���Q<{�t���"����rZ�e�#�F�#��m�@k$Մ�ç��D�t~��vu�G@L�1O�`0�4���Ӛ�h�#����r/�{��IR��=�j�dt\S��zigh��K �NT�B�2�FQ�*J�E��]4aQ��)�(T`at_i-խx\�������k������V9�;��C��7�|��a��e�ŗ�WW�K[P��9fn��A�y2��wiNiꉕؠI�D�X�#7�ht�x�͵�-�%�	�Zg�qV�6�r�v���p���0d��v8b�}vHء�v��C�
�`�g��)~��T���(ΰ�m�A;ء�=v��A�C�D;�v�H!��×ٝm�]�*�,)0}�jmR��6� +K�+DT��A� �,/�~�<����/�����C��T(��g_�#n�o�:�v�~�r�ţd �J=c�A��3Q,�h�u�5�i#��a�Fh5B��F��HU�1`��q#D� a�I#�,o��Gi��&M_�L�Eԙ�N/2M����gp����0nŞW<�����R��h3�4y�v��zl�FЙ�9�>���Z���>��W�������N�����
��
h��|�}9���#�Rl�@�;5>|��W����^�C|e>��z�6���iLy���i�z���`���#��6W����6+������k�*��6��6 �Ͻ�� �{�_�o��*��nx�Ƨ��k�˟AEII�.��;JJx���$�ʟ �o���\��[�����m8�w�vb2i��{�:�-�gY��Ec�Vw:�����2�qD] �`�IҬ������٘��?% [��N�����ǈ)���`vB ��JfJ��)G���P̽��/.������5ϣ����%��j��N�Z=c6ۭ9
���Z�F���f,0�@8g�j�P��	��;a�	�N8�}NH��2�p�[��U�I�s4#9�A���%�N�;!JT�'�@[Ţ'4Q�%WIj�L�P��e����+�V,��˱�M���DR��yW�����ᅇ�~��?^{ �;����#�u����g���enRą���9%v�CNK�[t:����f�^�`�7�e�@�"���a�W���&��-C@�{�;��L�x>� ���*�)����/_��+*�[*(�U�qFc��\�r6c�q�1ס�C���^fQ�A1~��lV�U��BժŐ^D�1m�6�7m�������.�� �׷�{��Y�"<��e%8����> �QE��$�w�F>�t-��=f���1���h�G�qy�1�ˑ�0��6��0Bϐxz�T��� ����� -�gMj)��5�̂g�����Ů�|�r�����*���-7�[����O;J�/��l9�:sI�h2�>�DZ�[�1c�����h��Yuz0�	8<����C�<�`���<�x8��i�x8�����5�#�����^
����⟦m��3����� �}�[�a�@'ٲ9��Ik?-��Ŕ,�o��ɻ�ڻ�ʍ��j���+�%�r�:���^N$xX���ڼE�yd��L��4^_�ݰ�����\��9���9� Ώ�D^���4���H5�WC�Z���j���
��^\5�T��j�D>J��MFV1I5���s��d��/�Y��z4���7�%�L�����i���R�2�3t�I:�:��j�WCE�̢���薯�e6b�}��aUw]� Ll�Su��Sz�����R����-]s]:'��@P����������ӓk���9��]����_��+W=��Ϟ-J�
Z2�n�|dF�����|bǦ-�[��͏>f�Y��Kt>�~���m��WV<�����t����R*�.۰�f׍{���ݷ�E?zP�>C=��(�f����{�9����LZ+ѭ��$?�v?l��O���Y?��'�p=�V/+��0�M����Cǧ~��~ꇧ�p�w�a�n��u��6z�}�����0�����~�ꇵ��)~p��3����E��h�}J�3�9�n]�"{<�t<ʽ�F�a�:�#��[�\���SF=n�ï���?q�6�9ݩ����ҫ��N"�;�Ȅ��-H�Z-���,W�0��je8�[޸l��@��ȟ�[���^O�u�����c{�n�f�RtӅM�X��/�߁k�kh��%#�jMf�@��Q'��µ��ʩi�.uZZ���{��4�d��h��CWʐ�qs����V�-��h� 90��9�̪H��ê���U��\��O9V�e5�h쉛�c'8/���b�J`��G��H��9�������|�N�ǋƎ��s�h��Zu� u����>���� �V�R����N�`�G(�Ȫ�
�D��)��4�j�AM~��hCG}0��U�
)A_g�#>8�A������>�}��Y��M���KIҗ$-�d�F4�vrCs'݂�@���Vʟ}�{w_^=��������_��Cl㬩�gFr_�����C>������ֱs5�'A�K��i�,q��Y�!��;1��uZky|�}'�r�CP{��7B�J�!8�#!��M!�	�7�\�E΅�l�B�Ak��2.�C�R~@�!��6�E��Ӵ
]���/;K�2]��-f����c�>�������4�!3��B`�t���
�L��.U���(� =!���rE�5g��^W���S�.0ڇ�N��,�)���i��ϔ������C����T79��Am`k�b�Z��d�4C����{�1� �L�������>�Ik�=J��"kj�Ӥ��I۬�B�4��4��b x�Τ����b�Z8�NK���m�̸|^�]�Is*�X1){%��(��3�}��N�#.���3DcyN�͆�^���ŴD}�Q�.�H�H�B_�FZ��D8��Y�E�j!%��	�}�]7'�2e*#��2?�װ��c�n��������چWV��!�i����+u���9������_S$���Q�W$i�D�J_L�c�}1�#��W�!i=p�(5���Ґ�T:Er��S�����D����c��
p94��$?	Ր/��(��!��QHkV�|��zy&_�`>���%��X��f��ٴ���c��hl���V��3��(�t�ܤ0��Jx3���:�.���ҳ'_������P�ɽo�u�ЙX+��]���O�����8����}���MtTh��})� E�'RԊޥ�w�Y;ZPN��쨞Qϣb �I74)t�,�-�C�IEhW�U���nE���]5��Fy�__?08�x]B>�O?�s{e�t��oc����r�٧��Xoñ�G:�(q2.�T?�
�R��>c��)3r�ަ��΍�a$g�0�Q�]1�Y�s�*N&w��M[11V���kU�2���P�Ӎ�ga�7��e��k�>�8�~�-�.lٻo��G��a=t>�?���-�KJ�mػy�d��ף�w�oX83<���6%Hy�Q^�t��H�d"g�l�f�񒪪Iks�����(8�u����۝��uK�C��������k>�VvUC�򛴏j�#���@4b���rQ��@	1�2�MI\�����-��������a�kP,h�������!��C���T{���'h�a����12z��4=X�� �63�6�0M1b�r��	#�����#�*zj��G��
=�:L��V�H,P�I'<B��i5�,@O�ަ��^F!��i?j�ô`5-��d����Q�E��0�F=Pá��}|�>��"�%.t&�sA]�i�dV�rDB�鄠�ġ+��0����f����W��z����k��/��3~q����`�x��0<z�N�05�2���+B*�2X�Y�8����J���}�}��?�FZf����t��	��/����1�\J�'���1�W���tWF�Uw��{8���~��+�����1E҇Ds3�L4~i`bK�:�7�\�]y���t��{����)L��?��9���n��1�K.za�nf>Pc��8��(�.r^z̉�� ��ڍ��-�x�I��X|k���`�QLuM(���M1ΦFhɊ��h��9������rPǑ����tP��r.���a0I�#���џ��'E���͓�{�~>s��1�������~��1��j���p(�pa��8�i&b���-c�ʭ����wE2,��k�LDK��ׇ���S��X�jBWcw�@]L)�O�� �`� ����W ��)��(, � *�9_ �
�4�;�U� 3R =/ � �u�M�d�)�NfEZd��M�A�y�~䑊Z�p���/=�a��w�xkr�8���G�ʎ�G7�M)�8,�g�y�Y�+�����W��Íys��!��ɳ\���4K�r���N�e��9�rU\7�
7�i8�	o�����$8��g.������m����ݦʲ�ʲ�<)u�8����aƗop�cVC�a��5";��7�Y�3kX�S�
�Nl�Kq�NS�,㰡�w�fU$���5CG,�zaMYg���(���10�+��?�I��ȋ*M}�b�D*�?v��c�(�bJ���m���bc3V�����{	��m�f���:�KZ��y�ً��i�6���"�D�Ǽ^g�W��.g;g�E8#BO:D�7}�����I������D�ut���!��x����9�,�0z�Mp�����s��~p�Ľ�J�K/�'���gS���`V��4���i]u#�o�Tg����6��3墢2u��**oBEe2q^��M1��3�c2�cG��&�|������UV_RA!(*�SAdOZK\���|聉VV�~�j��8�花�����zWs�%�\!���6����8�b�M1=���di���L6�*5~l��HG�E�!�١G��U��7��C��c�^L�`�y���
��;����T{��i�K��e�+S�t3�0㌆����'��ϭ0�!��`��:}��mp l��g+��Ď�L����,�p@���se(Ԁ]��k���j`HG5�O	�h���5��h ���$`5QD�������DR������d�_��.�k(�PMб���=��OcxP�?Dv��5��&�'Ϧ!f��)�XY��Q.�U�yА5yP��y`σ�<8�G�`_$�p>�|��*I�6�'����5}�xJ�����)^۹�XX�� |�t��p������hh~Y����?��-���ߐ�:y��;򋰗������{�hl���m�/�_Iy���w�;�u�7�^�����?0:���Ԅ��h�����tjۆ8*��	��]��	0E 'j-��g�
�sN
� �)ZC��� ��B� ���@ۇhup�6������QF8#�� =H�	J=>�`��F)��lk��B���Ʉ�����Ra:����RW7��пֺh��wq�X���}�aG�oo&^�k�O%��B�M:dB�ט�����r��D�7��&<|�Ó<��a5U<Xy��m�<�� H���a�Wc"�Z�� ��y�wxg�8*�'S��\l�]�[��i����,d����4ɻ�ލ��}/��{�n�qE��ט���o 5 �d�y��'G��G�/�b�){�Wk7s,o`�j����5� ���|���`��|`����N��J�Dv�DOu��i�z�;��u�3��4�<�/G��4RQvt�E��1y���|����'�	s�9��������	y���3[I!���� �5R�^��F��8~|�e�d`Py6�VY�5b�G����۩,1���F��Ւh��h��C��0��M1AǦ">N�#>r[���	N'%�W'�ᄟ;�1'��vZT�9N�B:?u��['<�o:A�6[i��Y'��	:�3TCA�i���"���$G)N4(����2��騑3ԥM��x��f ���m�z����47�.y�{�H��cI�I�Z��B>*?X!��bȋP�%p%��
��
�]hMI�j��[����@�ɉ_?P�d]�L@���~Qs������^�\|�d�� �[�ʵ�lȤ�m%���A�A�#�>|ي��t����A��Ⳋ�$v�G0��Y�Oq�c��X�(��E�|��S��z���X>a6F�3�����O#>�� �`�UXw+>R��و�U8�۰|#>��;��#�б�ؕyp7�ve<8��X���#��Wb��Q�R�.|J�������YK�8��1�������\����2�1�e���Ju���o�oXe�9g|�T`6��k鰜����̖o[d�!W�O��~�!9v�wƝw:O�nq=춸��zO��Y^kޯ���z�����>��v��?�/S.-!�q���<	�o���?G�Rꇮ/7d��s���CMM��w���ܚJkp��/��+y,�֑��ө��B8�6,I�s�֤�F�ϼ����J�7Ri3�`���䱋��s��xt�mL����J3����,���N�9��H�5$��5��?w4�֑��OSi=��9�JH�揩t���T�H���J�ȕK*m&W�J�-��p��s[g��V��9�,�t�\�۹�#!Nk�.�.�U&.��޶�M\�����ۜ���*�Yr1�lq-6Qߜ�).�j)]ٹ�M�׵�v��m۶k{s�⾖��ֶ^�D�������>%3�����b��b��>�YL�6���h�Z�n�<��m[g_����]���u�b�9�֕��ZņL����-m��֛hF��D��]��}��-Jo}��d�c]�mw�xys"����U�܇}��:���f�{::[:�=�}bk[_�.,�z�8�����8�������8��޶��ήmb�2�Tm1�ќP&��-���Ҽ}��ȳ=Xk+2iOg�;���'�j�#������D�:�M;U����۽���������;knm�ڹ�3��u4�6� Ől�-}�"H�����vWowO��+'q�*5����ƞ쮶�V�G���X	;���}�2���^hk��$k���]	��-6���đZ�-�v(|B2'҃kn��Ʋ���	leG_iG"�sY8�gϞ��kZ�3��r��������ѫ��c�Jd�º]���$�-[)��A������L1-��Jg��@2v�$�J�:��v�n��[IjH'نO��Hi%">͘o�T�&=�Z�K�:*�i���٤���G$K�˷c}uf7����f�n7�"�$��|}k�1�65�zZ{&��a�la%�ۊ���d�t��Ujn#�p�YL��V�RmT�m�+�@S}���8�2�+%���ߵ܉m���	Z��u����z_G��(������Zi�J��cŊҚ
-��.��p�Wc��X���2��B�VdBm��)�^��#h���s�Þ�̃KK�::�ݴ��)\��Ѳj����Ҭ����
-��H�~;h��ҳ��V��+Us+ʝ�������)�t�>v�F�ԙ��w;���va"����}��N͔�*�w`i�� |;�]�Zg;�*j_[S+i]����d��P��|�
POPE�������n���,�t,��Qf�FG�����ߊ5�ӾձuP�h��mK�:Ag��Wkj�ʨ{(���R�PV|[��W��Xy�U
f˦�t�}Ymw�Ѷf�R[�ڞ�I��v�����ʛJ�V�Z�Wм��&�굛���T���ՍuwQ~��I��ė(�L�۝��C�R"5�t}tP	�!��m��)�T�WMKj͔���_�S��C)��>z3cفc\�Z�]�U�+k��9�u�J�/zR�S���xQʪ�Xk���f]4U;1���飴,�s؆嫱��ԎV}� i%��7Do�6��H.	@���&��� �[²j|/���.����"|� |>*� ~W����p��e��w8�/��L��
~}hB��r���{i�]��Z|צ��0�o�hG�_ N:#c���c���~��|�|<:=�����ꏚ>z�#��#�~z��A��=~�ͱ�&�7��x{�[�������-��[eoE��+���-`׿�:��8\6�3�?|fxdxtX�����̏����c'V��{��?���3��2����C���/ܿ�������{F�a�B�cꞃհ�,D�:���\��qZV���g5>����D����<��n0�齳����<t����[na���g����n�/:=��U�Z:#�����"�z-v���b�֢iu�&)ЄH�6�6.�ȍ��kp�"Z� [Ůf�����N�6���g$:e���Tg]X^͞��V���=��������X���������-�6-�G�_ݓu/ԱR��p�T����{�;#��X���z���>l�2Vk�u�U�a����S0p�a]q�S��+���$ܚ,Z�|Kk6&��&�����|+���;H�oEr���d�[�lń�$�1���;Iu��/QL?P\��]�M�w#pK�
%�rR�}���h%(V�<�w�R� �`�-}D�R
��JJ��Ts���E�-�g��
endstream
endobj

13 0 obj
14069
endobj

14 0 obj
<</Type/FontDescriptor/FontName/BAAAAA+LiberationSerif
/Flags 4
/FontBBox[-543 -303 1277 981]/ItalicAngle 0
/Ascent 891
/Descent -216
/CapHeight 981
/StemV 80
/FontFile2 12 0 R
>>
endobj

15 0 obj
<</Length 507/Filter/FlateDecode>>
stream
x�]�ˎ�@E�|��b]݀G��<�X�"œ��� �a��ߧo�N"ea���.E�=�C�d?�=�%=�C7��x�[����#i׷K<����LI���_�y\���g8w[�G���Ɠ��d�����pI�~m���x��O�Ò�I]��?�:_��[s���z>t�t�<�Ö����S�cC�v��mjZ?7��'�<���~_'~��;W��r:���&D���:���`Kށ�r��e���l���hf�\	�E�,��k��z�-�xG��odݻg�������5C�ӿR���i����o��Kܗ��胡����G����։�8���菼п*��/��W�#�ܯD�пԽ���GVd8K�ǳ�[�_�ou��%z.�/��/�I�����Y�k!o�_�?6�?p��wp������-�_�ǲ�������m�W���-���_�>��2�����:���{��_T:8qB0B��?����yc��GLb?��ߊi��K�I$�
endstream
endobj

16 0 obj
<</Type/Font/Subtype/TrueType/BaseFont/BAAAAA+LiberationSerif
/FirstChar 0
/LastChar 66
/Widths[777 666 722 889 556 500 500 250 333 443 500 500 277 389 500 500
500 333 722 277 443 500 500 500 443 777 722 277 500 277 722 500
500 500 500 500 250 500 333 443 443 500 500 500 443 556 333 333
610 500 500 556 722 563 722 666 610 722 563 333 722 250 610 722
722 500 943 ]
/FontDescriptor 14 0 R
/ToUnicode 15 0 R
>>
endobj

17 0 obj
<</Length 18 0 R/Filter/FlateDecode/Length1 16152>>
stream
x��z{|ձ���۲�V/+ZY~%~ȉ�~Yqlǉ���q��$�b˱Il	KNHh�
!�P��mҖR(+�B胄W�����R��-�m/�	����w�he�!m�������wwΜ9s��̙3笓�#Q�CF	K�=���/�7�o����=I��׭D�,!�o��;�����	�N�:�s���ޫZBH�nB
�����'�,!����~D��TX�������u�7x�'�o��Ww�z"�o��r
˭���ⷰCH�0��t�U!���X"�,)�"dŸT������2�Q^v=� ҕ��R*3,�P���.G�k0��y+o�;��|���-���/�!b%1�*b���.v�8ȣ�L��J3O�i����R����%ϓ�  ��N�Kb�Sd�԰������"�@E�~%���b�#�NJ�i������<E.��qw��ȸ��z�u'<MЋ<$�M��z%V�5�@�%��s�{g�o�V�)�-r�<"˗K�A-�Q�'d���LO�Z���#7akz)V]z�h����6����\OM��h��LM�� ���q����#��I^E)�k�����Ŷ=�e���J��Bb?fL�g���O]�����F�g}(o��5���x�ث�+r�%h��"��uu�:�7�m����|US�����j�֬	V�^�r��eK�,^4��_YQ^ZR\T�+�z��ѐ��i5j�R��h�r!�[$��#�:_���\����V�����)!"����(�I	a!U��H:�
"e�e��4ep���J�R��'�^��	'�scj}!!����0WLz,x�؂J%I+ԥ���ՅQF8�Ӯ���j+��q�AB�R_�8��
0�uˏ3D���ő�EzS�;�j]^o��|}*�WK��Z�2�\�RQ�$:9(/?=v�I#�.����F�v���c��ƾ�2����jSs��eǑGS�ںT�ĵq�t?�3]BJQd�	c'8�;�fc"2FYd�;���6�:���G]��������X�����`����ס�Ik�89����T����1��C���75��6vu���z�?����y����i��TMP-�԰�+���� ف���ƎtY ;\����,�b�R��L��]���L7�ж�mc)�h}��5~0�݁�u�d�1�����3��e��P���BJQ�J�V��o�&cFZ�� �zǅ���2��������ߞ~;2P�eiG�ܑ
�"���;^���0l��3���S_ʹu%���:h�Yʲ6E�=r�����+�n,\�A�����$	L�=�Pp= I�V"�ע�׍u���<aW/λ>���MChᐯ#��54���:G�����6_��Ύ�� �
�WTw_�+�0�.R��!�B=����L���xQ�+9n�J�\$C�b��
u�Z�N*�b���imC��R*"��.oț�*��䎱�ZRjC�
�V��?�6P��K���B�/����T��C���eYT粭6�*e)�D�X�)H�L՗����ZG��ņ˪�g��1���mLb��|}�H.\jr�X Mh�^��S�N����4���KL|�{�|m+)5ƓO��K}�I#4n��(��Vs�7o<���:;�4bnx��G`ֆkB����I�� �2VBJA*H�6aAM�]O	��E�r�I ������d�8c��b�Q�0Xåk�jq�4n���u�H*jAuP�a��8H�G�}�.4@�=��c�M}F�k��4�(R���>�u{g�c9�B��;��.t{?��:�Wr�O����!i�M���j4�o5
��Ii}њ��W#�%|u���*tQ�����[S y@W������k���d��1�+P8���	��'2l�'z�٦0+�5�9d5��}s��R�ii�<�h�H� x��V��V/��B�Ǽ�Š���-}o�絤:PF��G�����-3�_`~,,��WP»�f�.Zb*Y��
T&>� ����ϝ����٭�<߷>��lk���~j�~��x�U��{M���׈aO��
+�v!��=�ٵ��o�Թ����Z�hKQ�s�86ޜ�T�Y`�9�iu,k����Sx��<p�<��`���<�)�S�)�D�?b�������{ ���Hy���x`�qZ�ꁠ�f��%�*��*�v��k8m���az� %4���0��d$靶5�Y���W) MbU��/ȕ��(`C�f���5���� P+
�G7n^Y�(^�t�1��s�CF�o˥ط�X���gl��=�Fީs�7�Ϣ/.�kssU,�g�sz��%�	��ܤ�6��^v���	0M���/2�UC���Lk�5��/�q��#w��ǋ�]5�v���kMɯ�?��55�vk���n3����h��X,�Z��q;�CnL�,���h٬:�´)�(����������<p���P��*c�T�|�,�Ʃ�dkx�{�(��R-�#{��D���,y�,,�&��|9����Zඋ���45m+����5������J3��o�^0��N�W�5� �S��G1舍���!f%Q:����Z[B,_耷��Z,t -�8z<�U~�g����; � ‣���-�`�q�����4L���P

i�J�d��죯��ۗ_9��/��״^�rUSK�>���?��ݏ�}��o��O�=L�O-�l�cr�Mw��l�)m�|��9�4�uJ�ՆaΪ���M!�����87�Ϲ�7$���F�����p�)7�)��Ӵx�q7�������?�裵��gt+�W6'�dN�Uh��+�H)�,/1��9s̅�ROTJ%�;��l2�FBf3�.(p$B*V��X����ev?�I�M�j��_�$�p8�Y:�/ZX�EKV�"j)�L�! �,J�~_��/�?��u����nܟ��ڣ��yʮ�=rl��'~Z
u�̿��ϪU��ʽ��G�y��|�I|��,sqL�4(�(V�<2����L*���0��հ�P�ZÚ�t��9h�*+�@�p�
��p�
�V�[��
X+XgE���9�I֑�+��5�J�� ����6W�¶������^��b��`�x�G�w��K6�:�(C����#��hlv֞�V�C[��Ur���n�ـ%�*�W��C��Ȍ?ɲuo�֍¢���LY�Þ@L�*/��p��d4�I0
�J����M0 ��|��̿a�Ͽ9��k�����Y��*��Z�g:�7ŗ�?������8�O���Ѓ�s5���*�Z��éQ�C�Yo��!��;df���;�7s¨Z��w��	SN8�	'pB�	A''\p�Y'�v�a'Ĝ�M�)��t�i�#�M���`���t�)Z՝ip�"_���;��g��B�&c�2����'�B��R�̤8�����{WK��ψ��9Yt�i78E�M;0���[\��-�8ן����ap��O����FL'����|��y.U��!�U���T>��T�E�"Ewh@-��A r�P�gvt���7s-�z��Ic%�[H���&t ˰�-�W�p��987q��T�4��L�q� k����
�K;*�}�<�#�w��~���<T�w��7���NQ�8��}e~͹}��օo�=�d����]��v5��%��?�S��Ċ+k$�ܡP�9s�<n��ɵ��Nb4j7��<�[B�x>+��<)�I��3�Ͷ�"�RS-���k�� �ҟ^Al8���J���zH̫ڽ��%m:󫟮\񚹌}��l2~�35e�N~�^�s߾ip���F؟��D�3*
�Y����'�N�6��*���q>ş�/�k15�,�1��ʵj�jJ*�(Ye�xHF��B-6�v�a�e
�ً��Z�x��c������p���u⃟YR4��� ��1'�(���ϫM.�k0�4,n��C:Π&��k���e�Z#�3�[Fx���#�f�W�E���P��)݉r3%}�V��i4Se��(��{vr:k:�Q����}fe
߬����'��w_�M�G�?3N)����9�����؃:��s���.��U7�*.L�8�@�"�z���7��#�ss����s8�`6�Rsʉ.���bહw�{�Sp��߆�Fv�����''��b�����Ә*���8��l�*�$9JS��f���!K^��;��U��o�,g�ɋ��n61�fp������S?����S�	�I��a��������x��O�@+~ >ˌ���e�!��]��W1�[p��.�N�^��6�J�q��b N�٪�4���:N����/�l�!��dR,fSi#a��ٱT!�>��H���'�aD�,�B����.6�c��Էo��+�c���������M�ѵ�Y
��52��hzޖ���i��.Xh�hpϧP��Z�
b0�2�f̬&7'��1cN I�N��f*�*1�>�/Kr�>Ό�\z�����1�s�9ׯw^,�_���x�;i�S�(�D�(�\&F���ix֔g�)�X=���y�\wA��.�rAV����(��˔��1�p����w�w�����Ŀ����90���|��J�]�۟?�����;�G��T�P6;�	>D�W;sXV�k���f���z���uJ�F�����9�"�m�Z�ƌ���\��tN�脷��~����(]��j��r}*�=��x蒾l*��!C=�E�B���h�� [3��W���nz2]�����	 ��3�k�P��� ���.��KD�� ��s||2z�����6v�c���o5,)��X�����+����䣣Z�����ģ�Q�C
�=��w�����<̷�x�'J�p)(��R𗂧�p�^,�S���G)A��K���J�MZ{���Ƨ.MW�[�b:�q�W�*M��5�E�}�'#�'0�����e��:l���J��( m;r ���jX-����&ޱ�/z��i��R��3A'������dXʾ7�/V�E׍��<��탴q��W޷o{����|��A��ȭ�6�C��5��9�Q�����y9yᐩ"3�c�Q��p����;�2s�pH�q���;�.r�p��.R���ny^���CO�h�ن�( ��j�,�B�KyMAJ���yܞ.!��K�5�B����.�ʻ(���Ы���N���ɋ��1)&��:'�unqГY�
��&�2�e`��s�y�Q0�BW6;�ϯZ�H����d��'�?	>,�w"�R\\x�!�!}��~�:��9��H�*�C�5��c:8��Q�� ��4&�����4��A��:�q���i{fU/���;Es_>�9}���
��E屒��J�V�B�6A�zm��#6v�Gl�l�m����l���ӷ��4A��1dD��8��_�%N��D�����	Y,��]��Pǚ`gg&k��5�`uW��R��I�.Vxe�^�R���ZsKH�5�Xֱ1�����&�0�Jt��޽�Y0��i�_��\�g)K�Ί��/~t������
j�/���c;����ѽgF|�}�a���ޟ��Q5S��߱O�LE�`��n�1���X!��))�وɔ�2��V��Riy%�RZ��S{R��%p�FK \Kp�����l��=�5o&$��ه�r&�>8)�q
&f5,ZHw�VC�*3T� "�������3[��������k�mls�qeUm+��xi�k���E%`���*���G�`�m,�}��՗^�WO�c�F���D�^�RY�].�YV��oe	T �^I�������C�v#�����y01̃�<�-��۬r�u����@�ID�P��D�p�����YӦMo�y��MO�k�}�+�n�4v������H���7�m���a�׾�5���o\�����ã���r�,�-��#��Q~�Z��v��=�`В�¹ڹ���y͡rC��n��-��r�K���M!���z�y�?���f?��a�������~x���Ï�p��쇛���Co������e��I�����rQf�NP7�am���P����g2��a�(A-���a)r�w?�iJx��!LŨ�l��}�A�s~H��!?�ig�T̗�Rk+FiE���@�Ӌ`w�i��1D������i�����(r����D�9�WX"y޳�y��4�X��!Q:k\S�a�6Դg:�ߟ}�8oޒ�B�d��3H�ԟ������wj1�6X��f�ҍJ)��q����E:]��D�$�� &�*p��-��2Vx�3�9 � �c���`����1R��a�VV,��za���5.^���+��*ޱ�� Vf��fr����){ͥG�x҆{���K>�ʦ�%��y����B�0:��%��5r���x��Ff��%���R>8�8-}P��g_�fm��d��mū@��&��0g��l�|�篿4S�r�S�K�i{G�����E�����/����j���\�^���e�s���?���J��"�d>YE���zb6�X�_�0�bV(q���+/B�j3ѩ9�Ѹ�%䛋��)�nkȝ�X�R1w�6�HC�_�T�-������!tnyo[bS����W�`�d~�`p��>��� h�L�H�G_�Y�<���~�-�L}�u�z��~v���6�����k�5k�WCW�k_}Р��}��sG�ir���1�W�y�m�Z�Qwpc0���3�H�#�G*m4�L�hyޤq8�����!�t�FCF��U��_�`|��B�a7��ׅV�<���T/�|F�#�INgE�Q =�q�����.���Q�c�)g���Ó��'����F���h����A�N�6���r��8�-���2�Uz+�%�b�V�Z,Ĳ��1g0�Z��S��!yX��\<�x����<����xx��y����<��+C\ƃ�פ�Ϡɐ�<<Di��aW��Oi���˔�fQf3��`��CY��,zd���}���2'xH���塊�Bo����p'�<`�fjyXH	����<0aZ�9m�-3�����+���u��
�L-�m3�$��w�|���`������Ǉ`~��ܾW~�O|�~��kl��_�z{c�|W>x�c��W8uIу~�%v� �Or�\��A��ݳJ�UU��Y{��S-&��[�>�*�Q��l/��n�����@H|\|T��O�ݯC.~K?�&�'Ŕ�q�Kot�W�S�S��δ�=���UX�u4W�j�0DV�WY�V�Rt��&K���*����ާ�LRC��t�]/SO���ަ.�v.lc�n�����,����oS��E���N{Am) _�v��G����������m�Yֿ��t.c��l�m۬�UM��@�g�G�z�v���́埆�<��x����>��F�c���c�Lϛ�ȗw�vV�������+ra�?Hŕh�CH��Fa;�W���oY�?�g��2܉'���8�|�x ܌�%��
�%�-DP������?�"�xK��X��a҇|z�Ƈw	��!����}X��,#�xWHm�]�&���E	���q����^�w!�M%LB=��(�8�W�)�̝T,P|Q�W�n�m��8Ր�Z�~Fs���Vi���Bg�}%Ǩ��?������n,6����K�j\c�_ߌ�/��3s�@�T;��u�eZ_��[d�!�aםkd��]�2� ��+2�$���~�CV��Y,��dXC�!�:���x���+��˰�,b�2�K�l�$==�g�e���d�!j�L�1��2̑y܀+H>w�+I)7!�*�>���I��g2�!���ɰ�yCi�aY�~[�s�V�O�����%5��9���z#Ɉ����ٟJ{�
��W	�b�������p<6IĆ*�k/'[ lB�d��~���i`G4M+�E��jb�{�$z�C��a�B���� �o�'$̂ʪ��E3$��B��j6�"Br8���b}����;��0"���ʶJ�5��%��P��y�aK_�@O�"{���ǒ�(�5#��ށ��D��X��Җ��
WE��h"6TI`_(�恡X�\��?��/�$��hb`�V��'�n#`m�24ۃ,�D�Q��h�`h����I�����4��hrx�'�{�>4�`[�@[�H�cǃф��+l�F��[�uӇ��ñ=TƊD�p4:��Ez#;v$�[d8҃C��$�FPB<2TQ72�GQҫ�5���im&b��`��P4�+��b���F���Xl�4���0
ڛ�Ȓ�/6�Ħ1!�ۋGm�zF%;����"=�1���$��`��?��/�����[�MӃ��D��V��������nB�I����Ѷ�Ih��~�Q8A&(2�9�r���q �LT&vWƆw�[�H- ;�N⽟DI/��`9�P��8�G�)U?bR�ع�^@�p�Q��:��a�nl/��c+��|cd�TbR��_r[��&Y�ں��ؾ94a�X��W m3��1����@�(���:�T���Z��za���KL�,@٪�WI]����iW�m �
T�IZ#�?��a�q1*�?֏�tQj��Di��r�x�#E�j�-%�$ioC�j�zl���}�l����<$�9�p���k�k)�v��%��O��ʾ�F��C����r���`9!�+���T�b%]�EI�~�)��쥭%��[�@/�i?��6"�e���G�RjS.뻏>��!�C��e|&�o��)B���� �&)m�w�o�<�Q+�v��j/����)_�4�{/���ې���xF+i��}V�m���(2z����F��JP�F��b7�;-[?���mT�u�� ��^y���q�� u�/���uz5ƍ�+rLk0�7t��ǜ�=D��cZ��n���w���k�>}������*�����n�r�1*Q/��O�VێP{��Sڛ���\��7&��c��WZ�A:?����rL8�(����~�=kz�9S)���_���SfϏ�iYQ�&y�MϺ�����DƠ&/���˚.� ͚���|�o�e�H{� ��T��e%�N�o������)/y�\�Z�O<%����~�I���f�&����� ����k�,�+aE�U�_�啈_�!ԀO?��x��#|�i��Əo�\��r9���'�[�V#Vzc&�^'��_��:����&API���y�`����I ���_r��?���f�L��h'gP�3UgZό�I�Q������~ݿ:�+��WP�x�y�F��������[O�O�O�O���!'��D����x��'����;��Z�z�}d��cx���� � �=�=U���{���=�/U�q}n���3q�����72Gnύp���9����0�$�S�D��'���Z7�q��� ۮd�<����ԟ�g#�^��n��v������[�ne�:�<�N ��N�H�N��	ys�G�!'�a��6�fO�*u����Ě4nf�Z��lX'xl���Q�:�:&������&0��v�(��7L���p��H5a�𠀓p��液�Ɠ��M�)UkW
nN�I���Δ��i���8p[��C�H��1���#v�S�%`��8OjB�D��^�(+K��˶'h9��R���%�o,$����Fg��%�$�$���t'�<"5��!b{!l ����,�lio�����6�
endstream
endobj

18 0 obj
9831
endobj

19 0 obj
<</Type/FontDescriptor/FontName/CAAAAA+LiberationSerif-Bold
/Flags 4
/FontBBox[-543 -303 1343 1007]/ItalicAngle 0
/Ascent 891
/Descent -216
/CapHeight 1007
/StemV 80
/FontFile2 17 0 R
>>
endobj

20 0 obj
<</Length 391/Filter/FlateDecode>>
stream
x�]��n�0��<E�ݡ��Z�B�h+q؏�� ��i(��~��6i��v>%���P�~�_���0��w��m���.����o�eE��ڌQj��6��rݰ�E�[ػM~�����/ނ��E�>�:���8~��$��(��.�yj���
1U�+��i^�����y�h-Y�,�Ʀ߸D�$)��t*"p��^��s�~6>�ʐ�$yRV�[�Y#kb�AΘOȆ����)�XQ�-qF}�Ěr9N9%3��3C>��B>1��2��x�d��Df�n��3���)��3�/�_��_S>�k�a��j���Y�o�$�����D^�)���R�c���G��ɑ�_�+��)�����?�顗�'Ǚ�%�޽cD�K��;���q���o���#
endstream
endobj

21 0 obj
<</Type/Font/Subtype/TrueType/BaseFont/CAAAAA+LiberationSerif-Bold
/FirstChar 0
/LastChar 38
/Widths[777 556 500 333 556 500 556 500 250 666 722 610 556 443 443 500
250 569 777 722 722 722 943 666 666 569 277 277 443 500 389 833
556 556 500 777 722 722 1000 ]
/FontDescriptor 19 0 R
/ToUnicode 20 0 R
>>
endobj

22 0 obj
<</Length 23 0 R/Filter/FlateDecode/Length1 13408>>
stream
x��z{|Tյ�^�1�$3s&�3�0g2�ey�2�!$!��f@L�̄�̐@��hm� �Vm����zm�&�%�i���
[���B���Uh/z{��|k�9	�R��}���L�9{��^{��:��n�T2Dx���Fwmڰ�r��um�+�oT��!܎����o��,!B!�'��m�^�u6!�3��􄃡%���o*�׃�~�6=�kp>��?~�~Α����
r�5���%������U��2��r���	I�F#��[�	B|	�G���q~uڃ0�=P>���Q�7M)�if�U��g�eG�3�5c&�����G�-��N���E���d���L|Lg��u���R��rȧ�i?"�$ϐym:6�A���{�,y�qE~nXņ'���e��?���`����qDaU��E} l3���6��`e�s�����Z�jw9E�rJ��N\�5�2�+w���:_��F�y��9PKb�I�0cCy��s�p��G�r*>�>'�:>�H������a�9Et�{0'�`�I��0����7p?��q�u�� ��ػ���l�Q{@$w��BA.��O���A�M�F�F�:�*���ʝ#��p��ӽ���[&>M2��*l%v�mC/��Ѯ�����o�ӿ|��@{[kKsSc�5W�ZyՊ��u�5˪����,��r����U̝�+).���͙����33$�Ŝ�b2�:Q�9 EJ:k|�"����`}q�R��SS\T��L(A%�7!�[_�@�`B�T�xNw&���}	�?����RI*���8V�U�`uS;�w�xJ�6����\6IÉǃL+��R����3\ۉ:�h�i�wY�T\DFM)8L�Q"���%�\~��Q�ҨX�im0�hlj��qy<��	���-�e�eB�,�g,�^�:٥��s�J�u�������	>���|���	�0Q�I��^&�<�(���&
)ו�SrV^		1��U�?%��'_	j]��SB�	nY��=�pա����J�p�pplbh�W�z�GSS���hn�؎,�&���J��HX;{`Q@�z]��DzӚ��S���U^��G��i�g�͂�A{<����dNCM�ɹBֹ��0��:�ʑ�{]�\�"���oW��'��!o-Z|W01��ku�ך0��x�m���`�
j�"ԫ$�\4RM'���$�V61��}�B��MY�E6�O���S��ғ�4t}a2Z������jG���"؉�a�L���D��zʻT��ޖvF��%2�%Hg�F��ղ�Rj�;k�*P^ަ��I�ĩ�r��D)'��,/�(˭nu'ܝ��]����$��p��аC�r���Xim_��]ٴ�}��Hr��rj/a�mw%�` &9��s�D�"@�Á���	}�O+�Ai�VW*��"�بF�@��hxt~S��Ӳ�In::E>��]��'yq��h���@�Z?��e
�����2����{�%�ol�{��aV֌�l������4c����''Ԙ��B�t�&���Դ�����ʰ���e�2�j	j�"Ah�H.VhB{��*VLi��ã~?M�E��wEh���^ɰ���⺉ʲ�������K[��v4��aG������hm?����:0:�ڟV�3(G�H'
�PN�810|��~B�ت� l�5���0 ]c\fM
�e����!���fH�����o��џʥq�Q��Cy��F O�B�F�����`h��w%1�ß�pG��m�۟H%HƮ(��.�=�l|��*!(7z�;4و���?H�w	�ɻѥ&L�pu"�[M�U^���(\�!
2 ���14ִ{0%���t[?��
`Q����;��H)��<��?Mǉ<�"/ ���d���2�l�t��I�<�1!|~�*��x��b�y��m8�yY�W
I'���N�OE����E��`�x�m�Q;t�a��v�DRUU(���L_�H*2��E���T� ��D����ST�涍�����S_��7���dǯ6������:}[�S�"�%��,b�t���4�h!�}��=�g��L��_&�Ń�SUV8m�eRyn�g�˖pe�{�7[g�FDRy�P�o���)���W����\[l��r�{�0�4N|,�-\����9�,I�Jt�!-���h�r����If�t�سz���W�@y�W�2�2E�[������@��P��'�-[��f����	E�
Փ�_������O��U�FX�6�B�/��6���g��n���e��4v���!�j�}S�Z�[�"��B����]���Z�֢�M]Po��=��*����3�J�-��^�7���6�`Y���4a��㖲%+bp���u8-]���8n����u��5�Q�N=g�:���ѭ�5ߺӳ��=w-��S������xoL���߿�1���=�ާ�{6��J���=���~��<��n����W���:	�{�\�x��m挂�fKi
جN�5f{��b4T�Z���B��Q����v�]kӂ�¶����܊�yUPAw���,A�v���v3�E�xu�z3g��%P;��8q���Z�YaTO�>z���
�(����ų6�M�-�=��_Yݿ$㑽�Op���7����zFݲ�Vw�Τz�orFN��W^��~�r-t��s�������YV�a�!?/���VG�aM����^>����Ck>\�'���|�;9��������x>���/�򡓭�M�6u���4Hj��*G����F��,><�����B��^�e�ħ>ԶQ}_˷�}������V?x��W�:`��������E����}s��/����Mtaߝ�i�c,\�o�2F����m����tc��FR��T�΍����=��}qXO%�t	T\�e�Q���f8���NC�_%�k&����?�}����iP��yp��;��,��_�w`#>Fr:;���Jh�=�����=?����6�$�2��*�))</�xW����=V��"�YĢ�ӥc[��)��
V�G�}.����.𹒮AW��	�[��c�F.�5e�6��a�*r�.�=sW�Uρ����_���^�BL�ߵ����;����������݊����+_�1X��qc�A�^��pe����
��9xǬ���]���t�]�Ip�V������sz=/7^�+`��|W �2�2_�����ȶ��A�@�m>�B��y%�&�����2d�,^p�8�I����m黮�/_w�ď>����7t�BW������P��'vߛs���_���k�����}��e����������Fp���8���k��x����(Z;�� �Fl��0�~#l7B��F8m��F8��CF���P��B��>�+<v|J#�T��0��k�ya��W�|Bh�L����L�^o0df9�4�i�c��ς=Yp&Y�G��t\YZU5-a���|�b��~�}�Tv.|t�c4��oo��]�}�ױO���O�I�h,^Љ��筒>�����TmEl_� .AH�	�IP.A����-�{�!���P���n	n�`���JP��gK`�@���S	�8I��d��`(a��TKP�(��H�.#xI�C<$�	n��o��F�y����2�~5����H�;��v��G�r%Ȑ@�H��o�$?��I	f�$�qu�&��&$���&��8�4�1z�q��q�2���rHo`y2U��������k/96]rL���4���li%�iə�N�Y<~�c=>�=|������`����o֙f< ��*��>�w
ߗg_��ý;���;����8��W��Lb�i4��o�+��n5[L.^i��b��U���<���أ�=zʓA����d�(+F�~e��:���$Q/t���z;�O�l����]kgݧ���m(����z�^J|�}�8�>���yL�+�"�EH��_��"t����E8��C�%EA+�7e�@<z���ώ����$���v����F;��ԥ5L&|Ndtfpi|F!RC ��,��� ��������i�dm�|��q͟����1����w�� �r�/2 ��T(<�sK�z�:�E�`{wN����� ��+�3�SSMi�4A�i�ND��Ag�R��ui�o`��$oE��2{�ݫ�T:x����V{�ر�*���;�/���/���a���l&ߊq�#,"vx�?�bJ7�%�͌5KvH&K��H�� q}�_s@�]���P���g��s�)w���r ��8k�~�r`s����g�~ဗ�����;`����& {R�gx��8 ���1�9L��`��0��I�s�0T�b>j�*�gs��x���u�#L'\��m�8�;ö����o'������/d{�%5aZ����1x��O�FG�n�zQVVU6���Ϋ`=�|�ˎ*H���^UQT�P���B����Υ�!Wm��i����r�{�*����#�8���~^,�c.��2��t\����C6Y�&|��BC ]��=i��ɶP{��,M6�RY)*���aɚ��+�L(����x�;��

�|�������_�t�]֧���^`�svD�M�~��Y,i�F��X�������E�J�ni�+�y��>Y���i�~������9���6`����1�Dߦ���Or���V��M��oo��Ǳ~}6v��'=2U���Y��g�X��U�%b���<����H<�89� :��_$MXVu���E]?�c[���XG���5�I��X7����z��ţ����m���,�������Ks��יL���32d��`�a�eX+C�W�P,�K�4�W��dxG��d������a��'�Wʰ���b�L����̽*��2<"�we�)×d觸kd�epʐ"�y>���dx���/�.�{�̭�aŽR�f� ��?+��?���T�.�k�;d��2r����(�I�RGd.���b{AY���*�����j�V�����;"�����Ee����z"�!=M0X$�I���7	����5!�����Zo���<��r9��d�nsLUw���s���H���)>?�#zԷM��?�������P���5�; p���}��U����o/�u;wx2V7c����~��h4��`�)����`�@�4X�^��@5)�%cs�z��9�Փ�h�mP���Ç������u�x_2?�~��ۍ�w4*��3x�h��$��F� ��=K�9B���Ɗ�����5�j�68�d4�
�љ��	N(w��	g�p�	�9�I'�r�����q���Nx�	�:a�nw�4:��	�	>r�K��'��,w�:�Na���q���h��7�g��^'ĝ�ҹ���q�l'�8��SL��NhpF�#N���'��p�>'D�`q68;��A�F>=5'R�R���v*�.�DǦ���壍�m�0�d`�C;H�;,�tn������^QT�£%3*���K�������Wv~�o�|�ƹw�m�����?���(�E:�&�>�]CH���l���U_Ӿ݄�4�F��3-���$#]g���-Z:�m(�d��A�b/�}_'��<ٷ}��ah7=�����_B�5���O�~�Sܫ�Q�}T�U�_���ϗ��3{�[�1���&)�I �N�x^�SĴT���48��Ҡ!�������d�W6�B���b�_����	w�w���?�^�ء�����X7�����N�gA�2}�4��'�r��l����MN����Lؓ	g2!�	�q4Ng���O`�g��œ[�5cG�� �w�����Tq�c��������;���ǆ{�,�R��G����v��+�,�T~ʹ��[�ي����O�S��l<���?
�]�^C�M�\t�B��%;������V!F*�8��G��F<�q>��;ğ�2zgs\�'ޭx�R8�#���6��F�n�!�.�ۉ03�oGٹ$J�$� 
���(_��?�!��C�ݍ�!�K�,C�1j<`�����S�H�Q��,RN�¬c%>r=!��|+�F�
S��vj�@,8�J am̓,ҫ��A���E��oicI'�����&2����.��Fb�:ml�^h��)d��ԯ�J���q�����L��J�#����@f	�6�AP�1Oʅ|m,�|�zm,����XGr���XO�
�hc����F2C|W��_��6N!ǵq*��h��id�1��ͤ�������ޛ�!%���Ht�`������U��Ι;GY���+�"���`0�(1-��TiF��x��b��dU�pWi	Ī#}�����@(<�+��^2U(������̙SRq�"S�iD�1%����ppp��Xe0��7"�w@i+i)Q���@\	���)��ޮ0v��AD��{P��{c��.*-V2��ii��������x8��Pj�t��?R�l����Q�cJ(�]?���)�(�ĽD� �-�"Ի{0��X�Ĩ]b���n���	�������ޮ`_�6�]Iס����{��`߁��h�n�����la�Ǻ�������ƑGOp0؅�B��vŘ1�J48P\�y0���-_u�J2���1�p8������E"�V�#��^(�S<M���@I#J0�=��"]�������I�]�\���ȥ?V��G�|[�n-	j^�B�� g��ŷEÚ+)���U����̵t-+V)Q�O*�hE�dd�-���@3�F㱒Xo_Idp���n�����8�7a�
� ΃8�"���� ��A�B�Z��R2���S!�+��}H��� ��Qv2�2@J���|1�R5kZ�3�"�@�.�
����t�
i�� ��j��!�Rw!� �)�B���b�/^U�x_�pbS����������P<���z�j�8[����}�lDX�t�]�3/�p%�f!ƕ�nC����(�e�L� �j����؍�]̣��]�7��$��{4o ��_c�I�&�C�����H�n�y5��y��U�<��+i��L^?Ψ-��&Tn�=C���ڀF��O�B9�F��2���&��4E����5���Ǔ�c��e~����,d�O��W���}�٦�]?�')u��Y[Y��L��=�̳l���n-N��8�t��^1��?̴�� ��uH���$��a1dk�3m'��vE5�2H1�e�@�=�Y�:��.�1i��c�������m��"S��X}����X5�8�neI���b�nf��&5�4
�'��dDE�v3�Z2��1���}#]W���.�,+zX�E�"�*}����蛞+]Z��h:����^Qf��Y18�K?�J����\�<-k'=т�g�Q-~�4�)�p��ri͜���^��d4��<��1[��=�������\���䑷�e��mPE �6X�ݫ��}���ݍ�+I,B���:y�g�䰷^��mx��>��^d)~�����<m�����hs/d3�lm^��x'�@;p�������q��C�<���Ч{>��)��3nߙ}g����;�q:rz�铧�?������b����ܿ?��}r�;m�[̷�w�ý|�oi
̢���U�ӏ'?qf��3�~�O��	��P�~�3ܿ�E����=�y���N�.�My�u��:�?��)��2��/����?[����lv^�x��?\�&c���&79�r���p��Ho{?|�8�?�Q��|�����8��7?�b���8č�n���T�ـ'OF�
��ӟ�[P�>�;Xup�A�r��ry,���c����<�=r��}�1��4� �P%�(�`�X�ρ�I%����rc����y����<���}u��}�:�-�un�=�{���亿��\�e�=�>22"�ug��a7X���)�:�N�N�k_��;�
�n���ۂ�7��3�gA\Q�p6
���)��D!���3�[�h��@�{��ԝ�mβ�6}ߦC������݁�V׻���s�Y}�{u�\wz��MD�
�|[�_�7�~;/v���%����2+/�u��Լ��oj��n���P��z�1����r�+���:�{9n��uh�Q�j�K�mXڬ��60bɄ{�C.#ެ�b��-U��v�`��,��e�r�2a�W!촅�h 0$�c�g����p�~�yeB߸&;9-��oZ���H���k�G�
|u�nR=se���=�93�2��p`�9*��@,�o.�����[�]
�Ba�X,��$I�0F
� �$��"S^��+��`��8Ebě��(�2bJ�M�g�����wb)�
endstream
endobj

23 0 obj
8426
endobj

24 0 obj
<</Type/FontDescriptor/FontName/DAAAAA+LiberationSans-Bold
/Flags 4
/FontBBox[-481 -376 1303 1033]/ItalicAngle 0
/Ascent 905
/Descent -211
/CapHeight 1033
/StemV 80
/FontFile2 22 0 R
>>
endobj

25 0 obj
<</Length 354/Filter/FlateDecode>>
stream
x�]��n�0��<E�ݡ����Bji�8�G�� ��i�(�o��f���Kb;_�e}�M?��nl/0��7��4�]�
��R	ݷ�:�;46}�e�fjӍy�o~m��"6=^�!_�כ��|�?�ܭ���,��(����yj�s3@HY�Z��~^�>�/�}� �%�����6-��� ȣ�yU�oM�9�ڵ���҇FQ�q��w�i�3g�	�DN�O���:�<#����!y~�\2��O�1�?s<լ8��,#f�#�?ý��5��"��x.��?"������_�$�'��
=%�Ǵ/�gT����.�el�������o-=&�)v�7����h1��o~��+
endstream
endobj

26 0 obj
<</Type/Font/Subtype/TrueType/BaseFont/DAAAAA+LiberationSans-Bold
/FirstChar 0
/LastChar 29
/Widths[750 666 389 610 610 556 889 277 610 556 556 277 610 722 610 277
556 333 556 333 610 610 777 556 333 943 277 722 556 610 ]
/FontDescriptor 24 0 R
/ToUnicode 25 0 R
>>
endobj

27 0 obj
<</F1 16 0 R/F2 21 0 R/F3 26 0 R
>>
endobj

28 0 obj
<</Font 27 0 R
/XObject<</Im4 4 0 R>>
/ProcSet[/PDF/Text/ImageC/ImageI/ImageB]
>>
endobj

1 0 obj
<</Type/Page/Parent 11 0 R/Resources 28 0 R/MediaBox[0 0 595.303937007874 841.889763779528]/Group<</S/Transparency/CS/DeviceRGB/I true>>/Contents 2 0 R>>
endobj

8 0 obj
<</Type/Page/Parent 11 0 R/Resources 28 0 R/MediaBox[0 0 595.303937007874 841.889763779528]/Group<</S/Transparency/CS/DeviceRGB/I true>>/Contents 9 0 R>>
endobj

29 0 obj
<</Count 6/First 30 0 R/Last 35 0 R
>>
endobj

30 0 obj
<</Count 0/Title<FEFF00500072006F006700720061006D002000640065007300690067006E>
/Dest[1 0 R/XYZ 56.7 266.339 0]/Parent 29 0 R/Next 31 0 R>>
endobj

31 0 obj
<</Count 0/Title<FEFF004100700070006C00690063006100740069006F006E0020006C00610079006500720020006D00650073007300610067006500200066006F0072006D00610074>
/Dest[8 0 R/XYZ 56.7 785.189 0]/Parent 29 0 R/Prev 30 0 R/Next 32 0 R>>
endobj

32 0 obj
<</Count 0/Title<FEFF006200720069006500660020006400650073006300720069007000740069006F006E0020006F006600200068006F00770020007400680065002000730079007300740065006D00200077006F0072006B0073>
/Dest[8 0 R/XYZ 56.7 598.839 0]/Parent 29 0 R/Prev 31 0 R/Next 33 0 R>>
endobj

33 0 obj
<</Count 0/Title<FEFF00640065007300690067006E002000740072006100640065002D006F006600660073>
/Dest[8 0 R/XYZ 56.7 398.689 0]/Parent 29 0 R/Prev 32 0 R/Next 34 0 R>>
endobj

34 0 obj
<</Count 0/Title<FEFF005700680065007200650020006D0079002000700072006F006700720061006D00200064006F006500730020006E006F007400200077006F0072006B002E>
/Dest[8 0 R/XYZ 56.7 267.539 0]/Parent 29 0 R/Prev 33 0 R/Next 35 0 R>>
endobj

35 0 obj
<</Count 0/Title<FEFF004400650063006C00610072006100740069006F006E0020006F0066002000650078007400650072006E0061006C0020007200650073006F00750072006300650073>
/Dest[8 0 R/XYZ 56.7 191.589 0]/Parent 29 0 R/Prev 34 0 R>>
endobj

11 0 obj
<</Type/Pages
/Resources 28 0 R
/MediaBox[ 0 0 595 841 ]
/Kids[ 1 0 R 8 0 R ]
/Count 2>>
endobj

36 0 obj
<</Type/Catalog/Pages 11 0 R
/OpenAction[1 0 R /XYZ null null 0]
/Outlines 29 0 R
/Lang(en-AU)
>>
endobj

37 0 obj
<</Creator<FEFF005700720069007400650072>
/Producer<FEFF004C0069006200720065004F0066006600690063006500200036002E0031>
/CreationDate(D:20220419235906+10'00')>>
endobj

xref
0 38
0000000000 65535 f 
0000072278 00000 n 
0000000019 00000 n 
0000001385 00000 n 
0000001406 00000 n 
0000032967 00000 n 
0000032989 00000 n 
0000033714 00000 n 
0000072448 00000 n 
0000033734 00000 n 
0000036353 00000 n 
0000073994 00000 n 
0000036375 00000 n 
0000050531 00000 n 
0000050554 00000 n 
0000050751 00000 n 
0000051328 00000 n 
0000051755 00000 n 
0000061673 00000 n 
0000061695 00000 n 
0000061899 00000 n 
0000062360 00000 n 
0000062681 00000 n 
0000071194 00000 n 
0000071216 00000 n 
0000071419 00000 n 
0000071843 00000 n 
0000072126 00000 n 
0000072179 00000 n 
0000072618 00000 n 
0000072674 00000 n 
0000072830 00000 n 
0000073070 00000 n 
0000073346 00000 n 
0000073526 00000 n 
0000073762 00000 n 
0000074100 00000 n 
0000074215 00000 n 
trailer
<</Size 38/Root 36 0 R
/Info 37 0 R
/ID [ <DB4C0FD2B75E64AB64A45D8A9D150BA0>
<DB4C0FD2B75E64AB64A45D8A9D150BA0> ]
/DocChecksum /895C207001380203E9189747E8E0D17E
>>
startxref
74390
%%EOF
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      