class Main : Object {
    run [
        | b := [ :x | r := x plus: 4. ].
          result := b value: 5 .
          str := result asString.
          _ := str print.
    ]
}

class Foo : Main {
    
}
