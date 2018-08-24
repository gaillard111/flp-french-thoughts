<?php
/**
 * Created by PhpStorm.
 * User: ars
 * Date: 03.08.18
 * Time: 11:34
 */

namespace ThoughtBundle\Entity;

use Doctrine\ORM\Mapping as ORM;

/**
 * Class GeneralMail
 * @ORM\Entity
 * @ORM\Table(name="general_mail")
 */

class GeneralMail
{
    /**
     * @ORM\Id
     * @ORM\Column(type="integer")
     * @ORM\GeneratedValue(strategy="AUTO")
     */
    protected $id;

    /**
     * @ORM\Column(type="string")
     */
    protected $subject;

    /**
     * @ORM\Column(type="text")
     */
    protected $body;

    /**
     * @ORM\Column(type="boolean")
     */
    protected $isSended = false;

    /**
     * @return mixed
     */
    public function getId()
    {
        return $this->id;
    }

//    /**
//     * @return mixed
//     */
//    public function getMailTo()
//    {
//        return $this->mailTo;
//    }

//    /**
//     * @param mixed $mailTo
//     * @return GeneralMail
//     */
//    public function setMailTo($mailTo)
//    {
//        $this->mailTo = $mailTo;
//        return $this;
//    }

    /**
     * @return mixed
     */
    public function getSubject()
    {
        return $this->subject;
    }

    /**
     * @param mixed $subject
     * @return GeneralMail
     */
    public function setSubject($subject)
    {
        $this->subject = $subject;
        return $this;
    }

    /**
     * @return mixed
     */
    public function getBody()
    {
        return $this->body;
    }

    /**
     * @param mixed $body
     * @return GeneralMail
     */
    public function setBody($body)
    {
        $this->body = $body;
        return $this;
    }

    /**
     * @return mixed
     */
    public function getisSended()
    {
        return $this->isSended;
    }

    /**
     * @param mixed $isSended
     * @return GeneralMail
     */
    public function setIsSended($isSended)
    {
        $this->isSended = $isSended;
        return $this;
    }


}