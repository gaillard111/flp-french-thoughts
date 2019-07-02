<?php


namespace ThoughtBundle\Entity;

use Gedmo\Mapping\Annotation as Gedmo;
use Doctrine\ORM\Mapping as ORM;

/**
 * @ORM\Table(name="dynamic_pages")
 * @ORM\Entity()
 */
class DynamicPage
{
    /**
     * @var int
     *
     * @ORM\Column(name="id", type="integer")
     * @ORM\Id
     * @ORM\GeneratedValue(strategy="AUTO")
     */
    private $id;

    /**
     * @var string
     *
     * @ORM\Column(type="string")
     */
    private $title;

    /**
     * @var string
     *
     * @ORM\Column(type="text")
     */
    private $text;

    /**
     * @var string
     *
     * @ORM\Column(type="string")
     *
     * @Gedmo\Slug(fields={"title"}, updatable=false, separator="_")
     */
    private $slug;

    /**
     * @var boolean
     *
     * @ORM\Column(type="boolean")
     */
    private $showInMenu;

    /**
     * @return int
     */
    public function getId()
    {
        return $this->id;
    }

    /**
     * @return string
     */
    public function getTitle()
    {
        return $this->title;
    }

    /**
     * @param string $title
     * @return DynamicPage
     */
    public function setTitle($title)
    {
        $this->title = $title;
        return $this;
    }

    /**
     * @return string
     */
    public function getText()
    {
        return $this->text;
    }

    /**
     * @param string $text
     * @return DynamicPage
     */
    public function setText($text)
    {
        $this->text = $text;
        return $this;
    }

    /**
     * @return string
     */
    public function getSlug()
    {
        return $this->slug;
    }

    /**
     * @param string $slug
     * @return DynamicPage
     */
    public function setSlug($slug)
    {
        $this->slug = $slug;
        return $this;
    }

    /**
     * @return bool
     */
    public function isShowInMenu()
    {
        return $this->showInMenu;
    }

    /**
     * @param bool $showInMenu
     * @return DynamicPage
     */
    public function setShowInMenu($showInMenu)
    {
        $this->showInMenu = $showInMenu;
        return $this;
    }
}