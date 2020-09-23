<?php

namespace AdminBundle\Controller;

use FOS\CKEditorBundle\Form\Type\CKEditorType;
use Sonata\AdminBundle\Admin\AbstractAdmin;
use Sonata\AdminBundle\Datagrid\ListMapper;
use Sonata\AdminBundle\Form\FormMapper;
use Sonata\AdminBundle\Route\RouteCollection;
use Sonata\FormatterBundle\Form\Type\FormatterType;
use ThoughtBundle\Entity\Content;

/**
 * Class ThoughtAdmin
 *
 * @package ThoughtBundle\Admin
 */
class ContentAdmin extends AbstractAdmin
{
    /**
     * @param FormMapper $formMapper
     */
    protected function configureFormFields(FormMapper $formMapper)
    {
        $formMapper
            ->add('title', 'text')
            ->add('content', CKEditorType::Class, [
                'config'    => [
                    'toolbar' => 'toolbar_for_content',
                    'filebrowserBrowseRoute' => 'ckeditor_image_upload',
                    'extraPlugins' => 'imageuploader'
                ],
            ]);
        ;
    }

    /**
     * @param ListMapper $listMapper
     */
    protected function configureListFields(ListMapper $listMapper)
    {
        $listMapper
            ->addIdentifier('contentType')
            ->add('title')
            ->add('content', 'html')
        ;
    }

    protected function configureRoutes(RouteCollection $collection)
    {
        // All routes are removed
        $collection->clearExcept(['edit', 'list']);
    }

    public function toString($object)
    {
        return $object instanceof Content
            ? $object->getTitle()
            : 'Content';
    }
}
