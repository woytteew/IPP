<?php
/**
 * IPP projekt 1
*
 * @file parse.php
*  @author Vojtech Czakan
**/

ini_set('display_errors','stderr');
$xml_stack=[];

parse($argc,$argv);

#Hlavni funkce scriptu
function parse($argc,$argv){
    #kontrola argumentu
    if($argc > 1){
        if($argv[1] == '--help'){
            echo("Skript načte ze standardního vstupu zdrojový kód v IPPcode23,\n");
            echo("zkontroluje lexikální a syntaktickou správnost kódu a vypíše na standardní\n");
            echo("výstup XML reprezentaci programu dle specifikace v sekci\n");
            exit(0);
        }
        else exit(10);
    }

    $header=false;
    $order=0;
    global $xml_stack;

    while(FALSE !== ($line = fgets(STDIN))){
        #Vymaze komentare
        $line = preg_replace('/[#].*/','',  $line);
        #Vymaze bile znaky na zacatku a konci stringu
        $line = trim($line);
        #Vymaze prebytecne oddelujici bile znaky
        $line = preg_replace('/\s+/', ' ', $line);

        if($line=='') continue;

        #kontrola hlavičky
        if(!$header){
            if(strtoupper($line)==".IPPCODE23"){
                $header=true;
                echo("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<program language=\"IPPcode23\">\n");
            }
            else exit(21);
        }
        else{
            $split= explode(' ',$line);
            $split[0]=strtoupper($split[0]);
            echo("\t<instruction order=\"$order\" opcode=\"$split[0]\">\n");
            switch($split[0]){
                #<symb2>
                case 'ADD':
                case 'SUB':
                case 'MUL':
                case 'IDIV':
                case 'LT': case 'GT': case 'EQ':
                case 'AND': case 'OR':
                case 'STRI2INT':
                case 'CONCAT':
                case 'GETCHAR':
                case 'SETCHAR':check_num_op($split,3);
                               check_sym(array_pop($split),3);
                #<symb1>
                case 'MOVE':
                case 'INT2CHAR':
                case 'STRLEN':
                case 'NOT':
                case 'TYPE':check_num_op($split,2);
                            check_sym(array_pop($split),2);
                #<var>
                case 'DEFVAR':
                case 'POPS':check_num_op($split,1);
                            check_var($split[1],1);
                            break;
                #<var><type>
                case 'READ':check_num_op($split,2);
                            if(preg_match("/^(int|bool|string)$/",$split[2])){
                                array_push($xml_stack,"\t\t<arg2 type=\"type\">$split[2]</arg2>\n");
                            }
                            else exit(23);
                            check_var($split[1],1);
                            break;
                #<symb1><symb2>
                case 'JUMPIFEQ':
                case 'JUMPIFNEQ':check_num_op($split,3);
                                 check_sym(array_pop($split),3);
                                 check_sym(array_pop($split),2);
                #<label>
                case 'CALL':
                case 'LABEL':
                case 'JUMP':check_num_op($split,1);
                            if(preg_match("/^[a-zA-Z_\-$&%*!?][\w\-$&%*!?]*$/",$split[1])){
                                echo("\t\t<arg1 type=\"label\">$split[1]</arg1>\n");
                            }
                            else exit(23);
                            break;
                #<symb>
                case 'PUSHS':
                case 'WRITE':
                case 'EXIT':
                case 'DPRINT':check_num_op($split,1);
                              check_sym($split[1],1);
                              break;
                #bez argumentu
                case 'CREATEFRAME':
                case 'PUSHFRAME':
                case 'POPFRAME':
                case 'RETURN':
                case 'BREAK':check_num_op($split,0);
                            break;
                default: exit(22);
            }
            while( $xml = array_pop( $xml_stack ) ) echo($xml);
            echo("\t</instruction>\n");
        }
        $order++;
    }
    echo("</program>\n");
    exit(0);
}

/*Kontroluje zda se jedna o konstantu nebo promennou
*
*@param $sym        vstupni retezec
*       $arg_num    cislo argumentu
*/
function check_sym($sym,int $arg_num){
    global $xml_stack;
    
    if(preg_match("/^(int)@(-?|\+?)\d+$/",$sym)                 ||     #jedna se o ciselnou hodnotu
       preg_match("/^(bool)@(true|false)$/",$sym)               ||     #jedna se o boolovskou hodnotu
       preg_match("/^nil@nil$/",$sym)                           ||     #jedna se o nil
       preg_match("/^string@(\\\\\d\d\d|[^\\\\\s])*$/",$sym)){         #jedna se o string

        preg_match("/^.*(?=@)/",$sym,$type);
        preg_match("/(?<=@).*$/",$sym,$const);
        $const[0] = replace_spec_char($const[0]);

        array_push($xml_stack,"\t\t<arg$arg_num type=\"$type[0]\">$const[0]</arg$arg_num>\n");
    }
    else check_var($sym,$arg_num);

}

/*Kontroluje zda se jedna o promennou
*
*@param $var        vstupni retezec
*       $arg_num    cislo argumentu
*/
function check_var($var, $arg_num){
    global $xml_stack;

    if(preg_match("/^(LF|TF|GF)@[a-zA-Z_\-$&%*!?][\w\-$&%*!?]*$/",$var)){
        $var = replace_spec_char($var);
        array_push($xml_stack,"\t\t<arg$arg_num type=\"var\">$var</arg$arg_num>\n");
    }
    else exit(23);
}

/*Kontroluje pocet operandu
*
*@param $array      pole s operandy
*       $wanted     pocet operandu ktery chceme
*/
function check_num_op($array,int $wanted){
    if(sizeof($array)-1!=$wanted){
        exit(23);
    }
}

/*Nahrazuje problematicke znaky pro prevod do xml
*
*@param $string      vstupni string
*@return vraci string s nahrazenymi znaky
*/
function replace_spec_char(string $string){
    $string = str_replace("&","&amp;",$string);
    $string = str_replace("<","&lt;",$string);
    $string =  str_replace(">","&gt;",$string);
    $string = str_replace("\'","&apos;",$string);
    $string = str_replace("\"","&quot;",$string);
    
    return $string;
}
?>