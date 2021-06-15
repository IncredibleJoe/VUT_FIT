<?php

  ini_set('display_errors', 'stderr');
  $xml = new DomDocument('1.0', 'UTF-8');
  $xml->formatOutput=true;

  $header = false;

  $labels = 0;
  $jumps = 0;
  $comments = 0;
  $loc = 0;
  $backjumps = 0;
  $badjumps = 0;
  $fwjumps = 0;

  const wrongParameter = 10;
  const inputFileFail = 11;
  const outputFileFail = 12;
  const wrongHeader = 21;
  const wrongCode = 22;
  const lexSynError = 23;

  $arguments = array();     //cmd arguments
  $files = array();         //files to output to
  $labelsUsed =  array();   //unique labels
  $jumpsArr = array();      //jump and call labels
  $statsArr = array(
    "labels" => 0,
    "jumps" => 0,
    "comments" => 0,
    "loc" => 0,
    "backjumps" => 0,
    "badjumps" => 0,
    "fwjumps" => 0,
  );

  //all cmd arguments are parsed to array, where these arguemnts are values
  //difference between getopt php function is that php function stores the parsed command line argumnts as array keys
  function customGetOpt($argc, $argv){

    //arrays for parsing the cmd line
    global $arguments, $files;

    for ($i = 1; $i < $argc; $i++){

      if ($argv[1] == "--help"){
        if ($argc == 2){
          fprintf(STDOUT, "Usage: parser.php [options] <inputFile\n");
          exit(0);
        }
        else
              exit(wrongParameter);
      }


      else{

        //if there is more than one cmd argument and it is not --help => --stats has to be firstone
        if ($i == 1){
          if (preg_match("~^(--stats=)([a-zA-Z].*)?~", $argv[$i])){
              $tmp = explode("=", $argv[$i]);
              $files[0] = $tmp[1];
              $arguments[0] = "stats";
          }
          else
            exit(wrongParameter);
        }

        else{

          if (preg_match("~^(--stats=)([a-zA-Z].*)?~", $argv[$i])){
              $tmp = explode("=", $argv[$i]);
              if (in_array($tmp[1], $files))
                exit(outputFileFail);
              array_push($files, $tmp[1]);
              $arguments[$i-1] = "stats";
          }

          elseif (preg_match("~^(--loc)$~", $argv[$i]))
              $arguments[$i-1] = "loc";

          elseif (preg_match("~^(--comments)$~", $argv[$i]))
              $arguments[$i-1] = "comments";

          elseif (preg_match("~^(--labels)$~", $argv[$i]))
              $arguments[$i-1] = "labels";

          elseif (preg_match("~^(--jumps)$~", $argv[$i]))
              $arguments[$i-1] = "jumps";

          elseif (preg_match("~^(--fwjumps)$~", $argv[$i]))
              $arguments[$i-1] = "fwjumps";

          elseif (preg_match("~^(--backjumps)$~", $argv[$i]))
              $arguments[$i-1] = "backjumps";

          elseif (preg_match("~^(--badjumps)$~", $argv[$i]))
              $arguments[$i-1] = "badjumps";

          else
            exit(wrongParameter);

        }
      }
    }
  }

  //check each argument given by array $arguments and each file given by array $files
  function checkArg($stats){

    global $arguments, $files;

    $argCounter = count($arguments);
    $statsCounter = 0;

    $file = fileCheckAndOpen($files[0]);
    //count how many stats arguemnts there are
    foreach ($arguments as $value){
      if (strcmp($value, "stats"))
        $statsCounter++;
      }

    //there is/are just --stats argument(s)
    //check, open each file and return them as empty
    if ($statsCounter == $argCounter){
      foreach ($files as $value){
        $fwrite = fwrite(fileCheckAndOpen($value), "");
        return;
      }
    }

    //first --stats is processed
    array_shift($arguments);

    //
    foreach ($arguments as $value){
      if ($value == "stats"){
        $file = fileCheckAndOpen(next($files));
        //there is no additional argument after --stats => output is empty file
        if (strcmp(next($arguments),"stats"))
          $fwrite = fwrite($file, "");
      }
      else {
        $fwrite = fwrite($file, $stats[$value]);
        $fwrite = fwrite($file, "\n");
      }
    }
  }


  //returns opened file for writing if the file given is valid
  function fileCheckAndOpen($file){
    $file = fopen($file, "w");
    if ($file === false)
      exit(inputFileFail);
    return $file;
  }


  //checks if the label is valid
  function checkLabel($string){
    if (preg_match('/^[a-zA-Z0-9_\-$&%*!?]+$/', $string)){
      htmlspecialchars($string);
      return $string;
    }
    else
      exit(lexSynError);
  }


  //parameter of this function is the argument of instruction, for example GF@counter
  //if $isVar != 0, arguemnt is <var>
  function ArgCheck($string, $isVar){

      if (strpos($string, "@")){
        $splitted = explode('@', $string, 2);

        if ($isVar){
          if (preg_match('/^(GF|LF|TF)$/', $splitted[0]) && preg_match('/^[a-zA-Z_\-$&%*!?]+[a-zA-Z0-9_\-$&%*!?]*$/', $splitted[1])){
          $splitted[0] = "var";
          $splitted[1] = htmlspecialchars($string);
          return $splitted;
          }
          else
              exit(lexSynError);
        }

        switch ($splitted[0]){
          case "GF":
          case "LF":
          case "TF":
            if (preg_match('/^[a-zA-Z_\-$&%*!?]+[a-zA-Z0-9_\-$&%*!?]*$/', $splitted[1])){
                $splitted[0] = "var";
                $splitted[1] = htmlspecialchars($string);
                return $splitted;
            }
            else
              exit(lexSynError);
            break;

          case 'int':
            if (preg_match('/^[+-]?[0-9]+$/', $splitted[1]))
              return $splitted;
            else
              exit(lexSynError);
            break;

          case 'bool':
            if (preg_match('/[TRUE|FALSE|true|false]/', $splitted[1])){      //Literály typu bool vždy zapisujte malými písmeny jako false nebo true.
              $splitted[1] = strtolower($splitted[1]);
              return $splitted;
            }
            else
              exit(lexSynError);
            break;

          case 'string':
            if (preg_match('/^([^\\\\]*(\\\\[0-9]{3})?[^\\\\]*)*$/', $splitted[1]))   //match everything except \, but \xyz where xyz are in range 0-9 accept
              return $splitted;
            else
              exit(lexSynError);
            break;

          case 'nil':
            if (preg_match('/^nil$/', $splitted[1]))
              return $splitted;
            else
              exit(lexSynError);
            break;

          default:
            exit(lexSynError);
            break;
      }
    }
    else
      //argument of instruction doesnt contain "@"
      exit(lexSynError);
  }

  //get the cmd arguments, array $arguments contains every argument as value
  //array $files contains files given (required by --stats)
  customGetOpt($argc, $argv);

  while ($line = fgets(STDIN)){

    //skip comments starting from the beginning of the line and possible whitespaces
    //which can occure before the .IPPcode21 header
    if ($line[0] == '#' || preg_match('/^\s*$/', $line)){
      if ($line[0] == '#'){
      $comments++;
      continue;
      }
    }

    //skip empty lines
    if(preg_match('/^\s*$/', $line))
      continue;

    //delete comments starting from other place than beginning of the line
    if (strpos($line, "#")){
      $comments++;
      $noComment = explode("#", $line);
      $line = $noComment[0];
    }

    //replace multiple whitespaces from the line with single one
    //delete end of line character from the end of line and
    //whitespaces from the begining and end of the line
    //split the line into array elements (line elements separated by space)
    $splitted = explode(' ', trim(preg_replace('/\s+/', ' ', $line), " \t\n"));

    //check if the code given has the required header
    if (!$header){
      if (preg_match('/^.IPPCODE21$/', strtoupper($splitted[0]))){
        $header = true;
        $program = $xml->createElement("program");
        $xml->appendChild($program);    //parent->appendChild(child)
        $program->setAttribute("language", 'IPPcode21');
        continue;
      }
      else{
        exit(21);
      }
    }

    //instructions handling
    //xml output
    switch(strtoupper($splitted[0])){

      //no operands
      case 'BREAK':
      case 'RETURN':
      case 'CREATEFRAME':
      case 'PUSHFRAME':
      case 'POPFRAME':
        if (count($splitted) == 1){
          $loc++;
          $instruction = $xml->createElement("instruction");
          $program->appendChild($instruction);
          $instruction->setAttribute("order", $loc);
          $instruction->setAttribute("opcode", strtoupper($splitted[0]));
        }
        else
          exit(lexSynError);
        break;

      //"var"
      case "DEFVAR":
      case "POPS":
        if (count($splitted) == 2){
          $loc++;
          $instruction = $xml->createElement("instruction");
          $program->appendChild($instruction);
          $instruction->setAttribute("order", $loc);
          $instruction->setAttribute("opcode", strtoupper($splitted[0]));

          $array = ArgCheck($splitted[1], 1);
          $arg1 = $xml->createElement("arg1", $array[1]);
          $instruction->appendChild($arg1);
          $arg1->setAttribute("type", $array[0]);
        }
        else
          exit(lexSynError);
        break;

      //"label"
      case "CALL":
      case "LABEL":
      case "JUMP":
        if (count($splitted) == 2){

          //case call or jump
          if ($splitted[0] != "LABEL"){
            $splitted[1] = checkLabel($splitted[1]);
            array_push($jumpsArr, $splitted[1]);
            $jumps++;
            if (in_array($splitted[1], $labelsUsed))
              $backjumps++;
          }
          //case label
          else{
            $splitted[1] = checkLabel($splitted[1]);
            if (!in_array($splitted[1], $labelsUsed))
              array_push($labelsUsed, $splitted[1]);
          }

          $loc++;
          $instruction = $xml->createElement("instruction");
          $program->appendChild($instruction);
          $instruction->setAttribute("order", $loc);
          $instruction->setAttribute("opcode", strtoupper($splitted[0]));

          $arg1 = $xml->createElement("arg1", $splitted[1]);
          $instruction->appendChild($arg1);
          $arg1->setAttribute("type", 'label');


        }
        else
          exit(lexSynError);
        break;

      //"symb"
      case "PUSHS":
      case "WRITE":
      case "DPRINT":
      case "EXIT":
        if (count($splitted) == 2){
          $loc++;
          $instruction = $xml->createElement("instruction");
          $program->appendChild($instruction);
          $instruction->setAttribute("order", $loc);
          $instruction->setAttribute("opcode", strtoupper($splitted[0]));

          $array = ArgCheck($splitted[1], 0);
          $arg1 = $xml->createElement("arg1", $array[1]);
          $instruction->appendChild($arg1);
          $arg1->setAttribute("type", $array[0]);
        }
        else
          exit(lexSynError);
        break;

      //"var", "type"
      case "READ":
        if (count($splitted) == 3){
          $loc++;
          $instruction = $xml->createElement("instruction");
          $program->appendChild($instruction);
          $instruction->setAttribute("order", $loc);
          $instruction->setAttribute("opcode", strtoupper($splitted[0]));

          $array = ArgCheck($splitted[1], 1);
          $arg1 = $xml->createElement("arg1", $array[1]);
          $instruction->appendChild($arg1);
          $arg1->setAttribute("type", $array[0]);

          if (preg_match('/^(int|bool|string)$/', $splitted[2])){
            $arg2 = $xml->createElement("arg2", $splitted[2]);
            $instruction->appendChild($arg2);
            $arg2->setAttribute("type", "type");
          }
          else
            exit(lexSynError);
        }

        else
          exit(lexSynError);
        break;

      //"var", "symb"
      case "MOVE":
      case "TYPE":
      case "INT2CHAR":
      case "STRLEN":
      case "NOT":
        if (count($splitted) == 3){
          $loc++;
          $instruction = $xml->createElement("instruction");
          $program->appendChild($instruction);
          $instruction->setAttribute("order", $loc);
          $instruction->setAttribute("opcode", strtoupper($splitted[0]));

          $array = ArgCheck($splitted[1], 1);
          $arg1 = $xml->createElement("arg1", $array[1]);
          $instruction->appendChild($arg1);
          $arg1->setAttribute("type", $array[0]);

          $array = ArgCheck($splitted[2], 0);
          $arg2 = $xml->createElement("arg2", $array[1]);
          $instruction->appendChild($arg2);
          $arg2->setAttribute("type", $array[0]);
        }
        else
          exit(lexSynError);
        break;

      //"var", "symb1", "symb2"
      case "ADD":
      case "SUB":
      case "MUL":
      case "IDIV":
      case "LT":
      case "GT":
      case "EQ":
      case "AND":
      case "OR":
      case "STRI2INT":
      case "CONCAT":
      case "GETCHAR":
      case "SETCHAR":
        if (count($splitted) == 4){
          $loc++;
          $instruction = $xml->createElement("instruction");
          $program->appendChild($instruction);
          $instruction->setAttribute("order", $loc);
          $instruction->setAttribute("opcode", strtoupper($splitted[0]));

          $array = ArgCheck($splitted[1], 1);
          $arg1 = $xml->createElement("arg1", $array[1]);
          $instruction->appendChild($arg1);
          $arg1->setAttribute("type", $array[0]);

          $array = ArgCheck($splitted[2], 0);
          $arg2 = $xml->createElement("arg2", $array[1]);
          $instruction->appendChild($arg2);
          $arg2->setAttribute("type", $array[0]);

          $array = ArgCheck($splitted[3], 0);
          $arg3 = $xml->createElement("arg3", $array[1]);
          $instruction->appendChild($arg3);
          $arg3->setAttribute("type", $array[0]);
        }
        else
          exit(lexSynError);
        break;

      //"label", "symb1", "symb2"
      case "JUMPIFEQ":
      case "JUMPIFNEQ":
      if (count($splitted) == 4){
        $jumps++;
        $loc++;
        $instruction = $xml->createElement("instruction");
        $program->appendChild($instruction);
        $instruction->setAttribute("order", $loc);
        $instruction->setAttribute("opcode", strtoupper($splitted[0]));

        $splitted[1] = checkLabel($splitted[1]);
        if (!in_array($splitted[1], $labelsUsed))
          array_push($labelsUsed, $splitted[1]);
        $arg1 = $xml->createElement("arg1", $splitted[1]);
        $instruction->appendChild($arg1);
        $arg1->setAttribute("type", 'label');

        $array = ArgCheck($splitted[2], 0);
        $arg2 = $xml->createElement("arg2", $array[1]);
        $instruction->appendChild($arg2);
        $arg2->setAttribute("type", $array[0]);

        $array = ArgCheck($splitted[3], 0);
        $arg3 = $xml->createElement("arg3", $array[1]);
        $instruction->appendChild($arg3);
        $arg3->setAttribute("type", $array[0]);
      }
      else
        exit(lexSynError);
      break;

      default:
        exit(wrongCode);
        break;
      }
    }

    $labels = count($labelsUsed);

    $compare = array_intersect($labelsUsed, array_unique($jumpsArr));
    $badjumps = count(array_unique($jumpsArr)) - count($compare);
    $fwjumps = count($jumpsArr) - $badjumps - $backjumps;


    foreach ($statsArr as $key => $value){
      $statsArr[$key] = ${$key};
    }

    //there is --stats argument
    if (count($arguments) > 0)
        checkArg($statsArr);

    echo $xml->saveXML();

?>
