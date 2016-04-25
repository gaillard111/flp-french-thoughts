<?php

namespace ThoughtBundle\Entity;

use Doctrine\ORM\Mapping as ORM;

/**
 * Class Content
 * @ORM\Entity
 * @ORM\Table(name="content")
 * @ORM\HasLifecycleCallbacks()
 */
class Content
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
    protected $title;

    /**
     * @ORM\Column(type="text")
     */
    protected $content;

    /**
     * @ORM\Column(type="datetime")
     */
    protected $createAt;

    /**
     * @ORM\Column(type="datetime", nullable=true)
     */
    protected $updateAt;

    /**
     * @var string
     */
    protected $formatType;

    /**
     * Get id
     *
     * @return integer
     */
    public function getId()
    {
        return $this->id;
    }

    /**
     * Set title
     *
     * @param string $title
     * @return Content
     */
    public function setTitle($title)
    {
        $this->title = $title;

        return $this;
    }

    /**
     * Get title
     *
     * @return string
     */
    public function getTitle()
    {
        return $this->title;
    }

    /**
     * Set content
     *
     * @param string $content
     * @return Content
     */
    public function setContent($content)
    {
        $this->content = $content;

        return $this;
    }

    /**
     * Get content
     *
     * @return string
     */
    public function getContent()
    {
        return $this->content;
    }

    /**
     * Set createAt
     *
     * @param \DateTime $createAt
     * @return Content
     */
    public function setCreateAt($createAt)
    {
        $this->createAt = $createAt;

        return $this;
    }

    /**
     * Get createAt
     *
     * @return \DateTime
     */
    public function getCreateAt()
    {
        return $this->createAt;
    }

    /**
     * Set updateAt
     *
     * @param \DateTime $updateAt
     * @return Content
     */
    public function setUpdateAt($updateAt)
    {
        $this->updateAt = $updateAt;

        return $this;
    }

    /**
     * Get updateAt
     *
     * @return \DateTime
     */
    public function getUpdateAt()
    {
        return $this->updateAt;
    }

    /**
     * @ORM\PrePersist
     */
    public function setCreateAtValue()
    {
        if (!$this->createAt) {
            $this->createAt = new \DateTime();
        }
    }

    /**
     * @ORM\PreUpdate
     */
    public function setUpdateAtValue()
    {
        $this->updateAt = new \DateTime();
    }

    /**
     * @return string
     */
    public function getFormatType()
    {
        return 'richhtml';
    }

    /**
     * @param string $formatType
     */
    public function setFormatType($formatType)
    {
        $this->formatType = $formatType;
    }
}
